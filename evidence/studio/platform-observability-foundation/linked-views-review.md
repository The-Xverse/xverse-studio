# Linked platform views: primary-agent component review

Candidate: `0e39680aef1186347c7b46142f5a620c9587e688`.
This is a source/component review, not independent milestone or platform acceptance.

The provider alone supplies the evidence root and frozen identities. Shared API,
reader and UI contain no Autoverse dispatch. HTTP selectors cannot supply paths,
writers, raw native records, executable metadata or codecs. Backend authentication,
strict selectors, frozen snapshot verification, separate run/plan/input identities,
source-bound immutable captures, finite cache/reader/page budgets and private-log
withholding were reviewed. Actual public Argus remains the authority; all three
views are derived. Native coalescing, dropped observations, upstream uncertainty,
source clocks and missing producer sequences remain distinct. Cause navigation
uses only original explicit IDs; ingestion order creates no causal edges.

One review finding was repaired: untyped native-input extension clocks could carry
nested metadata outside the declared browser policy. The final guard rejects
unsupported clock fields/shapes and invalid size metadata. The regression plus
fresh75 affected backend checks pass. The actual original237-record experiment was
read again through all three browser views on the final reader at1440x900 and
1024x768, including keyboard links, pagination, cross-tab cursor reset and bounded
keyboard table scrolling. Its original source witness is unchanged from the first
pre-UI capture. The evidence fixture's Studio metadata envelope was reconstructed;
this is not proof of original GUI launch or a new live experiment.

**Open lifecycle finding:** the Studio per-run worker closes public Core ownership.
A new owner correctly fences the predecessor durable claim even after actual prior
cleanup released. The second real GUI launch therefore failed before SDK acquisition.
No claim was deleted, private SDK handle constructed, cleanup uncertainty hidden,
or new runtime root substituted to continue activation. Studio needs a persistent
public Maestro owner across runs and an admitted recovery path for the already
lost-owner registration. Full same-candidate browser Start/Stop and Pygame driving/
cruise remain open. Original8878 preview/data are preserved. No task or milestone
state changes follow this component review.
