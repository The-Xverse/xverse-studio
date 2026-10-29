/** Studio-owned native FIFO bridge. Actual payloads traverse public C++ X-COM.
 * Single-threaded, parent-owned bounded stdio. No socket, path or command from XDL.
 * External transport publication and downstream consumption are separate receipts.
 */
#include "xverse/xcom/loopback_provider.hpp"
#include <nlohmann/json.hpp>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <initializer_list>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xverse::xcom;
using Json = nlohmann::json;
/** Copy an accepted public value; never dereference a failed factory. */
template <typename Result>
[[nodiscard]] auto need(const Result& result) {
  if (!result.has_value()) throw std::runtime_error("native public operation rejected");
  return *result.value();
}

/** Convert one validated hexadecimal byte nibble. */
[[nodiscard]] unsigned int nibble(const char value) {
  if (value >= '0' && value <= '9') return static_cast<unsigned int>(value - '0');
  if (value >= 'a' && value <= 'f') return 10U + static_cast<unsigned int>(value - 'a');
  throw std::runtime_error("invalid payload hex");
}

/** Decode at most128 owned bytes; no command text is interpreted. */
[[nodiscard]] std::vector<std::byte> decode(const std::string& text) {
  if (text.size() > 256U || text.size() % 2U != 0U) throw std::runtime_error("payload bound");
  std::vector<std::byte> result;
  for (std::size_t i = 0U; i < text.size(); i += 2U) {
    result.push_back(static_cast<std::byte>((nibble(text[i]) << 4U) | nibble(text[i + 1U])));
  }
  return result;
}

/** Serialize the exact visible bytes from an original ObservationRecord. */
[[nodiscard]] std::string hex(const std::span<const std::byte> bytes) {
  constexpr std::string_view digits = "0123456789abcdef";
  std::string result;
  for (const std::byte value : bytes) {
    const auto byte = std::to_integer<unsigned int>(value);
    result.push_back(digits[byte >> 4U]);
    result.push_back(digits[byte & 15U]);
  }
  return result;
}

/** Map original public accessors into Argus's versioned observation projection. */
[[nodiscard]] Json project(const ObservationRecord& record) {
  if (record.interaction_kind() != InteractionKind::message_event ||
      record.origin() != OriginKind::provider_generated ||
      record.payload_view_state() != PayloadViewState::complete ||
      record.provider_outcome() != ObservationProviderOutcome::accepted) {
    throw std::runtime_error("unexpected native observation");
  }
  Json result = {
      {"contractId", std::string(record.contract_id().value())},
      {"contractVersion", std::string(record.contract_version().value())},
      {"interfaceId", std::string(record.interface_id().value())},
      {"endpointId", std::string(record.endpoint_id().value())},
      {"schemaId", std::string(record.schema_id().value())},
      {"schemaVersion", std::string(record.schema_version().value())},
      {"interactionKind", "message_event"}, {"origin", "provider_generated"},
      {"sourceClock", {{"domain", std::string(record.source_clock_domain().value())},
                       {"unit", "ns"}, {"value", record.source_timestamp().nanoseconds()}}},
      {"observationClock", {{"domain", std::string(record.observation_clock_domain().value())},
                            {"unit", "ns"}, {"value", record.observation_timestamp().nanoseconds()}}},
      {"correlationId", std::string(record.correlation_id().value())},
      {"causationId", std::string(record.causation_id().value())},
      {"routeId", std::string(record.route_id().value())},
      {"providerId", std::string(record.provider_id().value())},
      {"sourcePayloadSize", record.source_payload_size()}, {"providerOutcome", "accepted"},
      {"payloadViewState", "complete"}, {"payloadSchemaState", "undecoded"},
      {"visibleBytesHex", hex(record.payload_bytes())},
      {"visibleByteCount", record.payload_bytes().size()},
      {"tapId", std::string(record.tap_id().value())},
      {"counters", {{"queued", record.counters().queued}, {"accepted", record.counters().accepted},
                    {"dropped", record.counters().dropped}, {"coalesced", record.counters().coalesced}}}};
  if (record.sequence().has_value()) result["sequence"] = *record.sequence();
  return result;
}


/** Reject unknown fields rather than silently interpreting a different protocol. */
void fields(const Json& value, const std::initializer_list<std::string_view> keys) {
  if (!value.is_object() || value.size() != keys.size()) throw std::runtime_error("fields");
  for (const auto key : keys) if (!value.contains(key)) throw std::runtime_error("field missing");
}

/** Read one finite, shallow host protocol message without unbounded getline. */
[[nodiscard]] std::optional<Json> read_message() {
  std::string raw;
  char byte{};
  while (std::cin.get(byte)) {
    if (byte == '\n') {
      return std::optional<Json>{Json::parse(raw, [](int depth, Json::parse_event_t, Json&) {
        if (depth > 16) throw std::runtime_error("json depth");
        return true;
      })};
    }
    if (raw.size() >= 65536U) throw std::runtime_error("message bound");
    raw.push_back(byte);
  }
  if (!raw.empty()) throw std::runtime_error("partial message");
  return std::nullopt;
}

void emit(const Json& value) {
  const auto encoded = value.dump();
  if (encoded.size() > 65536U) throw std::runtime_error("output bound");
  std::cout << encoded << '\n' << std::flush;
  if (!std::cout) throw std::runtime_error("output unavailable");
}

/** One independently owned native route, not a second authored system. */
struct NativeRoute final {
  CommunicationContract contract;
  EndpointSpec source;
  EndpointSpec destination;
  RouteSpec route;
  LifecycleController lifecycle;
  std::unique_ptr<LoopbackProvider> provider;
  ProviderComposition composition;
  std::optional<ProviderRouteHandle> handle;
  std::optional<ObservationTapHandle> tap;
  std::optional<Json> latest_input;
  std::uint64_t accepted{0U};
  std::uint64_t received{0U};

  NativeRoute(const Json& config, const Json& identity, ObservationHub& hub)
      : contract(need(CommunicationContract::create({config.at("interfaceId").get<std::string>(),
          "1.0.0", config.at("interfaceId").get<std::string>(), config.at("schemaId").get<std::string>(),
          "1.0.0", InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume}))),
        source(need(EndpointSpec::create({config.at("sourceEndpointId").get<std::string>(),
          identity.at("planDigest").get<std::string>().substr(7U), identity.at("providerId").get<std::string>(),
          EndpointDirection::produce}, contract))),
        destination(need(EndpointSpec::create({config.at("destinationEndpointId").get<std::string>(),
          identity.at("planDigest").get<std::string>().substr(7U), identity.at("providerId").get<std::string>(),
          EndpointDirection::consume}, contract))),
        route(need(RouteSpec::create({config.at("routeId").get<std::string>(),
          identity.at("planDigest").get<std::string>().substr(7U), identity.at("providerId").get<std::string>()},
          source, destination))),
        lifecycle(need(LifecycleConfiguration::create({2U, 1U}))),
        provider(std::make_unique<LoopbackProvider>(need(ProviderDescriptor::create({
          identity.at("providerId").get<std::string>(), "1.0.0", "studio.native-fifo-bridge.v1", 0x0FU,
          delivery_capability_bit(DeliveryCapability::best_effort),
          ordering_capability_bit(OrderingCapability::per_route_fifo), 128U, 1U, 1U})))),
        composition(need(ProviderRegistryConfiguration::create(1U)), hub) {
    const auto sh = need(lifecycle.declare_endpoint(source));
    const auto dh = need(lifecycle.declare_endpoint(destination));
    const auto rh = need(lifecycle.declare_route(route));
    static_cast<void>(need(lifecycle.validate_endpoint(sh)));
    static_cast<void>(need(lifecycle.validate_endpoint(dh)));
    static_cast<void>(need(lifecycle.validate_route(rh, sh, dh)));
    static_cast<void>(need(lifecycle.activate_endpoint(sh)));
    static_cast<void>(need(lifecycle.activate_endpoint(dh)));
    if (composition.register_provider(*provider).outcome() != ProviderOutcome::registered)
      throw std::runtime_error("provider registration");
    handle.emplace(need(composition.prepare_route(lifecycle, route, rh, sh, dh,
        {"1.0.0", InteractionKind::message_event, DeliveryCapability::best_effort,
         OrderingCapability::per_route_fifo, 128U, 1U})));
    if (composition.activate_route(*handle, lifecycle).outcome() != ProviderOutcome::activated)
      throw std::runtime_error("route activation");
    if (!config.at("observe").is_boolean()) throw std::runtime_error("observe type");
    if (config.at("observe").get<bool>()) {
      const auto route_id = config.at("routeId").get<std::string>();
      const auto provider_id = identity.at("providerId").get<std::string>();
      const auto spec = ObservationTapSpec::create({kObservationContractVersion,
          config.at("tapId").get<std::string>(), {{}, {}, {}, route_id, provider_id, {}, {}},
          ObservationPayloadMode::bounded_prefix, 128U, 1U,
          ObservationOverflowPolicy::coalesce_latest, ObservationValidityEffect::degrade_on_loss});
      if (!spec) throw std::runtime_error("tap spec");
      const auto attached = hub.attach(*spec);
      if (!attached.handle) throw std::runtime_error("tap attach");
      tap.emplace(*attached.handle);
    }
  }

  void close() {
    if (composition.drain_route(*handle, lifecycle).outcome() != ProviderOutcome::draining ||
        composition.close_route(*handle, lifecycle).outcome() != ProviderOutcome::closed)
      throw std::runtime_error("route cleanup");
  }
};

class Bridge final {
 public:
  explicit Bridge(const Json& config) : identity_(config.at("identity")),
      origin_(std::chrono::steady_clock::now()) {
    fields(config, {"kind", "identity", "routes"});
    if (config.at("kind") != "configure") throw std::runtime_error("configure first");
    fields(identity_, {"runId", "planDigest", "inputSemanticDigest", "providerId",
                       "installationDigest", "operationId", "correlationId", "clockDomain"});
    for (const auto& value : identity_) {
      if (!value.is_string() || value.get_ref<const std::string&>().empty() ||
          value.get_ref<const std::string&>().size() > 128U) throw std::runtime_error("identity bound");
    }
    for (const auto key : {"planDigest", "inputSemanticDigest", "installationDigest"}) {
      const auto value = identity_.at(key).get<std::string>();
      if (value.size() != 71U || value.substr(0U, 7U) != "sha256:" ||
          value.find_first_not_of("0123456789abcdef", 7U) != std::string::npos)
        throw std::runtime_error("digest");
    }
    if (!config.at("routes").is_array() || config.at("routes").empty() ||
        config.at("routes").size() > 32U) throw std::runtime_error("route bound");
    std::size_t observed = 0U;
    for (const auto& route_config : config.at("routes")) {
      fields(route_config, {"routeId", "interfaceId", "schemaId", "sourceEndpointId",
                             "destinationEndpointId", "observe", "tapId"});
      for (const auto key : {"routeId", "interfaceId", "schemaId", "sourceEndpointId", "destinationEndpointId", "tapId"})
        if (!route_config.at(key).is_string() || route_config.at(key).get_ref<const std::string&>().size() > 128U)
          throw std::runtime_error("route identity bound");
      for (const auto& previous : routes_)
        if (previous->route.route_id().value() == route_config.at("routeId").get<std::string>())
          throw std::runtime_error("duplicate route");
      if (route_config.at("observe").get<bool>()) ++observed;
      if (observed > 3U) throw std::runtime_error("observer bound");
      routes_.push_back(std::make_unique<NativeRoute>(route_config, identity_, hub_));
    }
    emit({{"kind", "ready"}, {"runId", identity_.at("runId")},
          {"clockDomain", identity_.at("clockDomain")}, {"routeCount", routes_.size()},
          {"observedRouteCount", observed}, {"transport", "native-in-process-fifo"}});
  }

  /** Each input makes one actual submit/receive before external publication. */
  bool process(const Json& request) {
    if (!request.at("requestId").is_number_unsigned() ||
        request.at("requestId").get<std::uint64_t>() != request_sequence_ + 1U)
      throw std::runtime_error("request sequence");
    ++request_sequence_;
    const auto kind = request.at("kind").get<std::string>();
    if (kind == "ingress") {
      fields(request, {"kind", "requestId", "route", "payloadHex"});
      if (!request.at("route").is_number_unsigned()) throw std::runtime_error("route index");
      const auto index = request.at("route").get<std::size_t>();
      if (index >= routes_.size()) throw std::runtime_error("route unavailable");
      auto& route = *routes_[index];
      const auto payload = decode(request.at("payloadHex").get<std::string>());
      const auto stamp = elapsed();
      const auto event = identity_.at("operationId").get<std::string>() + ".input." + std::to_string(++input_sequence_);
      const auto clock = identity_.at("clockDomain").get<std::string>();
      const auto correlation = identity_.at("correlationId").get<std::string>();
      const auto item = need(CommunicationItem::create({route.contract.contract_id().value(), "1.0.0",
          route.contract.interface_id().value(), route.source.endpoint_id().value(),
          route.contract.schema_id().value(), "1.0.0", InteractionKind::message_event,
          OriginKind::provider_generated, Timestamp(stamp), clock, correlation, event,
          route.route.route_id().value(), identity_.at("providerId").get<std::string>(), payload}, route.contract));
      if (route.composition.submit(*route.handle, item, route.lifecycle).outcome() != ProviderOutcome::accepted)
        throw std::runtime_error("submit failed");
      ++route.accepted;
      const auto delivered = need(route.composition.receive(*route.handle, route.lifecycle));
      if (delivered != item) throw std::runtime_error("delivery mismatch");
      ++route.received;
      if (route.tap) route.latest_input.emplace(Json{
          {"schemaVersion", "1.0"}, {"eventId", event},
          {"producerId", identity_.at("providerId").get<std::string>() + ".input"},
          {"origin", "transport-ingress"}, {"sourceClock", clock_value(stamp)},
          {"correlationId", correlation}, {"upstreamCausationId", nullptr},
          {"routeId", std::string(route.route.route_id().value())},
          {"endpointId", std::string(route.source.endpoint_id().value())},
          {"sourcePayloadSize", payload.size()}});
      emit({{"kind", "delivered"}, {"requestId", request_sequence_}, {"route", index},
            {"payloadHex", hex(delivered.payload().bytes())}, {"nativeInputEventId", event}});
      return true;
    }
    fields(request, {"kind", "requestId"});
    if (kind != "collect" && kind != "stop") throw std::runtime_error("operation unavailable");
    if (kind == "stop") for (auto it = routes_.rbegin(); it != routes_.rend(); ++it) (*it)->close();
    Json result = {{"kind", "idle"}, {"requestId", request_sequence_}, {"traffic", traffic()},
                   {"routesReleased", kind == "stop"}};
    const auto batch = collect(kind == "stop");
    if (batch) { result["kind"] = "batch"; result["projectionJson"] = batch->dump(); }
    emit(result);
    if (kind == "stop") {
      for (auto& route : routes_) if (route->tap &&
          hub_.detach(*route->tap).outcome != ObservationOutcome::accepted)
        throw std::runtime_error("tap cleanup");
      return false;
    }
    return true;
  }

 private:
  [[nodiscard]] std::int64_t elapsed() const {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now() - origin_).count();
  }
  [[nodiscard]] Json clock_value(const std::int64_t value) const {
    return {{"domain", identity_.at("clockDomain")}, {"unit", "ns"}, {"value", value}};
  }
  [[nodiscard]] Json traffic() const {
    Json result = Json::array();
    for (const auto& route : routes_) result.push_back({
        {"routeId", std::string(route->route.route_id().value())},
        {"accepted", route->accepted}, {"received", route->received}});
    return result;
  }
  [[nodiscard]] std::optional<Json> collect(const bool released) {
    Json records = Json::array(), inputs = Json::array(), snapshots = Json::array();
    const auto cutoff = elapsed();
    for (auto& route : routes_) {
      if (!route->tap) continue;
      const auto observed = hub_.poll(*route->tap);
      if (observed.status.outcome == ObservationOutcome::no_record) continue;
      if (!observed.record || !route->latest_input ||
          observed.record->causation_id().value() != route->latest_input->at("eventId").get<std::string>())
        throw std::runtime_error("native input provenance");
      records.push_back(project(*observed.record));
      inputs.push_back(*route->latest_input);
      route->latest_input.reset();
      const auto snapshot = hub_.snapshot(*route->tap);
      if (!snapshot) throw std::runtime_error("native snapshot");
      snapshots.push_back({{"snapshotVersion", "1.0"},
          {"handle", {{"hubInstanceId", snapshot->handle.hub_instance_id()},
              {"tapId", snapshot->handle.tap_id()}, {"generation", snapshot->handle.generation()}}},
          {"queued", snapshot->queued}, {"accepted", snapshot->accepted}, {"dropped", snapshot->dropped},
          {"coalesced", snapshot->coalesced}, {"backpressureRejections", snapshot->backpressure_rejections},
          {"experimentValidityDegraded", snapshot->experiment_validity_degraded},
          {"declaredTapId", std::string(snapshot->declared_tap_id.value())},
          {"validityEffect", "degrade_on_loss"}, {"validityState", std::string(to_string(snapshot->validity_state))},
          {"intervalProvenance", {{"streamId", identity_.at("runId").get<std::string>() + ".native"},
              {"intervalId", "pull." + std::to_string(batch_sequence_ + 1U)}, {"closure", "closed"},
              {"start", clock_value(previous_cutoff_)}, {"end", clock_value(cutoff)},
              {"provenance", released ? "actual-native-routes-closed; cumulative-counters" :
                  "serial-native-pull-cutoff; routes-active; cumulative-counters"}}}});
    }
    previous_cutoff_ = cutoff;
    if (records.empty()) return std::nullopt;
    Json witness = identity_;
    witness.erase("operationId"); witness.erase("correlationId"); witness.erase("clockDomain");
    witness["batchSequence"] = ++batch_sequence_;
    Json result = {{"projectionVersion", "1.0"}, {"upstreamContractVersion", std::string(kObservationContractVersion)},
        {"exporter", {{"task", "studio-native-fifo-bridge"}, {"toolVersion", "1.0"}}},
        {"records", records}, {"extensions", {{"io.xverse.maestro.execution", witness},
            {"io.xverse.native.inputs", inputs}, {"io.xverse.native.snapshots", snapshots},
            {"io.xverse.native.receipt", {{"traffic", traffic()}, {"routesReleased", released},
                {"transport", "native-in-process-fifo; external-publication-separate"}}}}}};
    if (result.dump().size() > 32768U) throw std::runtime_error("batch bound");
    return std::optional<Json>{std::move(result)};
  }
  Json identity_;
  std::chrono::steady_clock::time_point origin_;
  ObservationHub hub_;
  std::vector<std::unique_ptr<NativeRoute>> routes_;
  std::uint64_t request_sequence_{0U}, input_sequence_{0U}, batch_sequence_{0U};
  std::int64_t previous_cutoff_{0};
};
}  // namespace

int main() {
  try {
    const auto config = read_message();
    if (!config) return 2;
    // Heap ownership avoids placing the bounded native provider/hub arrays on
    // the small process stack. There is no dynamic queue growth.
    auto bridge = std::make_unique<Bridge>(*config);
    while (const auto request = read_message()) if (!bridge->process(*request)) return 0;
    return 2;  // Lost parent pipe is not a confirmed orderly native close.
  } catch (const std::exception&) {
    return 2;  // Never reflect private input or paths into diagnostics.
  }
}

