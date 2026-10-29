import { useRef, useState } from "react";
import type { ArtifactRegistration } from "../../../../../packages/contracts/api";
import type { Data } from "../../api/types";
import { api, mutationKey } from "../../api/client";
import type { DoAction } from "../../app/App";
export function ArtifactRegistrationForm({
  providers,
  onSaved,
  doAction,
}: {
  providers: Data[];
  onSaved: () => Promise<void>;
  doAction: DoAction;
}) {
  const [name, setName] = useState(""),
    [version, setVersion] = useState("1.0.0"),
    [kind, setKind] = useState<ArtifactRegistration["artifactKind"]>("model"),
    [identity, setIdentity] = useState(""),
    [origin, setOrigin] = useState(""),
    [providerIds, setProviderIds] = useState<string[]>([]),
    [apiVersion, setApiVersion] = useState(""),
    [license, setLicense] = useState(""),
    [limitations, setLimitations] = useState("");
  const key = useRef(mutationKey());
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void doAction("Registering inert artifact metadata", async () => {
          await api("/catalog/artifacts", {
            method: "POST",
            key: key.current,
            body: {
              name,
              version,
              artifactKind: kind,
              digest: identity,
              originRef: origin,
              providerIds,
              apiVersions: apiVersion.trim() ? [apiVersion.trim()] : [],
              ...(license.trim() ? { license: license.trim() } : {}),
              limitations: limitations
                .split("\n")
                .map((value) => value.trim())
                .filter(Boolean),
            } satisfies ArtifactRegistration,
          });
          await onSaved();
        });
      }}
    >
      <p>
        Record an immutable external artifact reference. Registration does not
        download, build, install, execute, flash, or grant device access.
        Availability remains unresolved until separately admitted.
      </p>
      <div className="two-fields">
        <label>
          Artifact name
          <input
            required
            maxLength={120}
            value={name}
            onChange={(event) => {
              key.current = mutationKey();
              setName(event.target.value);
            }}
          />
        </label>
        <label>
          Artifact version
          <input
            required
            value={version}
            pattern="[0-9]+\.[0-9]+\.[0-9]+([\-+][A-Za-z0-9.\-]+)?"
            maxLength={64}
            onChange={(event) => {
              key.current = mutationKey();
              setVersion(event.target.value);
            }}
          />
        </label>
      </div>
      <label>
        Artifact kind
        <select
          value={kind}
          onChange={(event) => {
            key.current = mutationKey();
            setKind(event.target.value as ArtifactRegistration["artifactKind"]);
          }}
        >
          {[
            "model",
            "executable-component",
            "firmware",
            "container-image",
            "data",
          ].map((kind) => (
            <option key={kind}>{kind}</option>
          ))}
        </select>
      </label>
      <label>
        Declared SHA-256 digest
        <input
          required
          value={identity}
          onChange={(event) => {
            key.current = mutationKey();
            setIdentity(event.target.value);
          }}
          pattern="sha256:[a-f0-9]{64}"
          placeholder="sha256: followed by 64 lowercase hexadecimal characters"
          maxLength={71}
        />
      </label>
      <label>
        Portable origin reference
        <input
          required
          value={origin}
          onChange={(event) => {
            key.current = mutationKey();
            setOrigin(event.target.value);
          }}
          maxLength={512}
          placeholder="urn:organization:artifact:version"
        />
      </label>
      <div className="two-fields">
        <label>
          Compatible XDL API version (optional)
          <input
            value={apiVersion}
            maxLength={200}
            onChange={(event) => {
              key.current = mutationKey();
              setApiVersion(event.target.value);
            }}
          />
        </label>
        <label>
          License or distribution restriction (optional)
          <input
            value={license}
            maxLength={200}
            onChange={(event) => {
              key.current = mutationKey();
              setLicense(event.target.value);
            }}
          />
        </label>
      </div>
      <fieldset className="provider-checkboxes">
        <legend>Declared compatible providers</legend>
        {providers.map((provider) => (
          <label className="checkbox-label" key={provider.providerId}>
            <input
              type="checkbox"
              checked={providerIds.includes(provider.providerId)}
              onChange={(event) => {
                key.current = mutationKey();
                setProviderIds((ids) =>
                  event.target.checked
                    ? [...ids, provider.providerId]
                    : ids.filter((id) => id !== provider.providerId),
                );
              }}
            />
            <span>
              {provider.name} ·{" "}
              {provider.available ? "available" : "unavailable"}
            </span>
          </label>
        ))}
      </fieldset>
      <label>
        Limitations (one per line)
        <textarea
          rows={3}
          value={limitations}
          maxLength={1600}
          onChange={(event) => {
            key.current = mutationKey();
            setLimitations(event.target.value);
          }}
        />
      </label>
      <div className="form-actions">
        <button className="button primary">Register metadata only</button>
      </div>
    </form>
  );
}
