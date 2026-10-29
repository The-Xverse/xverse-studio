import { Icon } from "../../app/ui";
import type { PendingStart } from "./control";

export function PendingStartNotice({
  pending,
  sending,
  onRetry,
  onDismiss,
}: {
  pending: PendingStart;
  sending: boolean;
  onRetry: () => void;
  onDismiss: () => void;
}) {
  return (
    <div
      className="notice warning pending-start"
      role="status"
      data-pending-start={sending ? "sending" : "unacknowledged"}
    >
      <Icon name="info" />
      <div>
        <strong>
          {sending
            ? "Start request sent"
            : "Start acknowledgement not received"}
        </strong>
        <p>
          {sending
            ? "Waiting for the backend to acknowledge the Start request."
            : "The backend may already have accepted this Start. Retrying sends the same request identity, so it returns the existing run instead of starting another."}{" "}
          Snapshot <code>{pending.snapshotId.slice(0, 18)}</code> · sent{" "}
          {new Date(pending.sentAt).toLocaleTimeString()}
        </p>
        {!sending && (
          <div className="button-row">
            <button className="button primary" onClick={onRetry}>
              Retry same Start
            </button>
            <button className="button" onClick={onDismiss}>
              Dismiss receipt
            </button>
          </div>
        )}
        {!sending && (
          <p className="hint">
            Dismissing forgets this browser receipt only; it does not withdraw a
            run the backend may already own. Check the run history in Results.
          </p>
        )}
      </div>
    </div>
  );
}
