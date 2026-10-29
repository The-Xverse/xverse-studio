# Before implementation

Four API assertions failed against the existing route before the events 1.1 implementation. A requested streamVersion=1.1 still returned legacy IDs. A matching run/snapshot cursor with an incompatible record proof returned CURSOR_INVALID rather than explicit resynchronization. A missing admitted journal returned a successful empty stream, and a corrupted journal returned a successful stream of its valid prefix. The new contract distinguishes those cases before response headers.

Only new isolated synthetic journals/metadata were used. The corrupt/missing cases intentionally affect their own disposable fixture; no existing run or provider evidence was modified. The full raw failing receipt remains in ignored local evidence; this directory contains its machine-path-sanitized copy. These failures precede repair and are retained rather than replaced by successor evidence.
