# Keyboard creation prerequisite finding

Full native browser cohort failed before the new project heading appeared. The screenshot showed focus remaining in Project name. Source inspection found connectStudio waits only for the authenticated header; loadBoot can still be busy. The Create project submit button is deliberately disabled during that operation, but locator.focus() does not wait for it to be enabled.

Controlled native Linux reproduction held the actual GET /capabilities during reload. The dialog remained open with the name filled. Create.disabled was true; focus() left focus in the name INPUT; Enter sent zero project POSTs. Releasing the bootstrap GET enabled the button. Explicitly focused Enter then created exactly one project and displayed its heading. No runs, provider execution or equipment were involved.

This confirms a missing fixture precondition rather than failure of enabled keyboard submission. Repair only neutral-assets-flow: assert Create enabled before focus, assert it focused before Enter. Keep keyboard activation, original heading assertion and timeouts unchanged. No click fallback or arbitrary delay.
