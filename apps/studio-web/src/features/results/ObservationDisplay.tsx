import type { Data } from "../../api/types";
import { receipt, sourceTime } from "./evidenceFilters";
import { Empty } from "../../app/ui";
function values(sample: Data): Data {
  const value = sample.values ?? sample.value ?? {};
  return value && typeof value === "object"
    ? value
    : typeof value === "number"
      ? { value }
      : {};
}
export function ObservationTable({
  samples,
  observations = {},
}: {
  samples: Data[];
  observations?: Data;
}) {
  const allKeys = [
    ...new Set(samples.flatMap((sample) => Object.keys(values(sample)))),
  ];
  const keys = allKeys.slice(0, 8);
  return (
    <div
      className="table-scroll observation-table-region"
      tabIndex={0}
      role="region"
      aria-label="Exact observation table scroll region"
    >
      <table aria-label="Exact recorded observations">
        {allKeys.length > 8 && (
          <caption>
            Showing 8 of {allKeys.length} value fields. Complete returned values
            remain in Input and evidence provenance; original immutable payloads
            remain in Events.
          </caption>
        )}
        <thead>
          <tr>
            <th>Emitter / observer</th>
            <th>Source clock</th>
            <th>Source tick</th>
            {keys.map((key) => (
              <th key={key}>{key} (declared unit per row)</th>
            ))}
            <th>Original time metadata</th>
            <th>Receipt UTC</th>
          </tr>
        </thead>
        <tbody>
          {samples.map((sample, index) => {
            const time = sourceTime(sample);
            return (
              <tr
                key={sample.eventId || index}
                data-observation-id={sample.eventId}
              >
                <td>
                  {sample.source?.providerId || "Not declared"}
                  <br />
                  {sample.observerRef || "Not declared"}
                </td>
                <td>{time?.domain || "Unavailable"}</td>
                <td>{time?.raw || "Unavailable"}</td>
                {keys.map((key) => (
                  <td key={key}>
                    {values(sample)[key] === undefined
                      ? "Missing"
                      : typeof values(sample)[key] === "object"
                        ? JSON.stringify(values(sample)[key])
                        : String(values(sample)[key])}
                    {sample.units?.[key] !== undefined && (
                      <small className="field-hint">
                        {" "}
                        (
                        {typeof sample.units[key] === "string"
                          ? sample.units[key]
                          : JSON.stringify(sample.units[key])}
                        )
                      </small>
                    )}
                  </td>
                ))}
                <td>
                  <code>
                    {sample.sourceTime
                      ? JSON.stringify(sample.sourceTime)
                      : "Unavailable"}
                  </code>
                </td>
                <td>
                  {receipt(sample, observations.presentation).label}
                  <details>
                    <summary>Original receipt</summary>
                    <pre>
                      {JSON.stringify(
                        {
                          eventId: sample.eventId,
                          recordedAt: sample.recordedAt ?? null,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
export function ObservationPlot({
  samples,
  observations,
}: {
  samples: Data[];
  observations: Data;
}) {
  const known = samples.map((sample) => ({ sample, time: sourceTime(sample) })),
    reported = Array.isArray(observations.facets?.clockDomains)
      ? observations.facets.clockDomains
      : [],
    domains = [
      ...new Set(
        reported.length
          ? reported
          : known.flatMap((row) => (row.time ? [row.time.domain] : [])),
      ),
    ];
  const domain =
      observations.effectiveFilter?.clockDomain ||
      (domains.length === 1 ? domains[0] : null),
    selected = known.filter((row) => row.time && row.time.domain === domain),
    keys = [
      ...new Set(
        selected.flatMap(({ sample }) =>
          Object.keys(values(sample)).filter(
            (key) =>
              typeof values(sample)[key] === "number" &&
              Number.isFinite(values(sample)[key]),
          ),
        ),
      ),
    ].slice(0, 4);
  const resolutions = new Set(
    selected.map(({ sample }) =>
      JSON.stringify(sample.sourceTime?.resolution ?? null),
    ),
  );
  const units = new Set(
    selected.flatMap(({ sample }) =>
      keys
        .filter((key) => typeof values(sample)[key] === "number")
        .map((key) => JSON.stringify(sample.units?.[key] ?? null)),
    ),
  );
  const incompatibility =
    resolutions.size > 1
      ? "Original source resolutions differ; no alignment is assumed"
      : units.size > 1
        ? "Numeric quantity units differ; use the exact table"
        : "";
  if (incompatibility)
    return (
      <>
        <Empty title={incompatibility}>
          Original metadata and values remain inspectable. No conversion is
          inferred.
        </Empty>
        <ObservationTable samples={samples} observations={observations} />
      </>
    );
  const missing = known.filter((row) => !row.time).length;
  if (!domain || !selected.length || !keys.length)
    return (
      <>
        <Empty
          title={
            domains.length > 1
              ? "Select one original source clock to plot"
              : "No comparable source-time points"
          }
        >
          Missing or incompatible clock times remain inspectable in the table.
          Array position and receipt time are never substituted.
        </Empty>
        <ObservationTable
          samples={samples.slice(0, 200)}
          observations={observations}
        />
      </>
    );
  const ticks = selected.map((row) => row.time!.tick),
    first = ticks.reduce((a, b) => (a < b ? a : b)),
    last = ticks.reduce((a, b) => (a > b ? a : b)),
    span = last - first || 1n;
  const numbers = selected.flatMap(({ sample }) =>
      keys
        .map((key) => values(sample)[key])
        .filter((value) => typeof value === "number" && Number.isFinite(value)),
    ),
    low = Math.min(0, ...numbers),
    high = Math.max(1, ...numbers),
    x = (value: bigint) =>
      55 + (Number(((value - first) * 1000000n) / span) / 1000000) * 820,
    y = (value: number) => 230 - ((value - low) / (high - low)) * 205,
    colors = ["#477ee7", "#2aa396", "#c89330", "#9769c3"];
  const discontinuous = (observations.gaps || []).length > 0;
  let nonmonotonic = false;
  return (
    <div className="exact-observation-chart">
      {missing > 0 && (
        <p className="notice">
          {missing} sample(s) with missing or malformed source time are omitted
          from the plot and retained in the table.
        </p>
      )}
      <p className="field-hint">
        Original clock: {domain} · tick unit:{" "}
        {observations.tickUnit || "Not declared"}. Exact endpoint ticks:{" "}
        {first.toString()} to {last.toString()}.
      </p>
      {discontinuous && (
        <p className="notice">
          Collection gaps are reported; points are shown without connecting
          lines.
        </p>
      )}
      <svg
        viewBox="0 0 900 270"
        role="img"
        aria-label={`Recorded observation chart in ${domain}. Exact source ticks; missing time is not plotted.`}
      >
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line
              x1={55}
              x2={875}
              y1={230 - f * 205}
              y2={230 - f * 205}
              stroke="#e7edf5"
            />
            <text
              x={48}
              y={234 - f * 205}
              textAnchor="end"
              fontSize={10}
              fill="#687b93"
            >
              {(low + f * (high - low)).toPrecision(4)}
            </text>
          </g>
        ))}
        <text x={55} y={255} fontSize={10}>
          {first.toString()}
        </text>
        <text x={875} y={255} fontSize={10} textAnchor="end">
          {last.toString()}
        </text>
        {keys.map((key, k) => {
          let previous: bigint | null = null,
            identity = "";
          const segments: string[][] = [[]];
          const points = known.map(({ sample, time }, index) => {
            const value = values(sample)[key],
              source = JSON.stringify([
                sample.observerRef,
                sample.source?.providerId,
                sample.units?.[key],
              ]);
            if (
              !time ||
              time.domain !== domain ||
              typeof value !== "number" ||
              !Number.isFinite(value) ||
              sample.gap
            ) {
              if (segments.at(-1)!.length) segments.push([]);
              previous = null;
              return null;
            }
            if (
              previous !== null &&
              (time.tick <= previous || identity !== source)
            ) {
              if (time.tick <= previous) nonmonotonic = true;
              if (segments.at(-1)!.length) segments.push([]);
            }
            segments.at(-1)!.push(`${x(time.tick)},${y(value)}`);
            previous = time.tick;
            identity = source;
            return (
              <circle
                key={sample.eventId || index}
                cx={x(time.tick)}
                cy={y(value)}
                r={2.5}
                fill={colors[k]}
                data-source-tick={time.raw}
                data-clock-domain={domain}
              />
            );
          });
          return (
            <g key={key}>
              {!discontinuous &&
                segments
                  .filter((s) => s.length > 1)
                  .map((segment, index) => (
                    <polyline
                      key={index}
                      points={segment.join(" ")}
                      stroke={colors[k]}
                      strokeWidth={2}
                      fill="none"
                    />
                  ))}
              {points}
            </g>
          );
        })}
      </svg>
      {nonmonotonic && (
        <p className="notice">
          Duplicate or non-monotonic source ticks are shown in separate
          segments; no interpolation or reordering is applied.
        </p>
      )}
      <div className="plot-legend">
        {keys.map((key, index) => (
          <span key={key}>
            <i style={{ background: colors[index] }} />
            {key}
          </span>
        ))}
      </div>
    </div>
  );
}
