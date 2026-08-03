# Studio Avatar Previewer StyleLink workaround

## Confirmed diagnosis

The warning originates in Studio-owned UI, not in the experience or avatar asset:

```text
CoreGui.AvatarPreviewerEditingToolbar.Wrapper.Children
├── StyleLink -> StylingService.ViewportToolingFramework
└── StyleLink -> StylingService.AvatarCompatibilityPreviewer.Design
```

Roblox documents that only one StyleSheet can apply to a given UI tree. The warning is therefore consistent with two direct StyleLinks under the same internal parent.

`CoreGui` is not replicated and is controlled by Roblox Studio. The warning does not alter GLB geometry, orientation, UVs, texture bytes, rigging, weights, mouthbag, teeth or tongue.

## Why the earlier diagnostic returned "toolbar not open"

`AvatarPreviewerEditingToolbar` exists only while the Avatar Previewer/Avatar Setup UI is open. A one-shot script executed while the window is closed correctly finds nothing. The operational fix must start first, wait for the toolbar to appear, and then inspect the exact parent.

## Safe session workaround

Use `roblox_studio/fix_avatar_previewer_stylelinks.lua` in Studio's Command Bar before opening Avatar Setup.

The script:

1. waits up to five minutes for the internal toolbar;
2. verifies the exact known path;
3. requires both known StyleSheets before acting;
4. keeps `ViewportToolingFramework` under `Wrapper.Children`;
5. temporarily sets only the redundant child link to `AvatarCompatibilityPreviewer.Design` to `nil`;
6. watches for recreation during the session;
7. provides restoration and stop functions;
8. makes no changes when the internal structure differs.

The specific child `AvatarCompatibilityPreviewer.Design` link is disabled because the toolbar already has an ancestor Design link, while the Children subtree has the ViewportToolingFramework link. This minimizes the change and avoids destroying Studio-owned instances.

## Commands

Restore the temporary link:

```lua
_G.RestoreAvatarPreviewerStyleLinks()
```

Stop watching without restoring:

```lua
_G.StopAvatarPreviewerStyleLinkFix()
```

## Truth boundary

This is an unsupported, temporary Studio-session workaround for an internal UI warning. It is not a permanent Roblox engine fix. Studio updates may change the internal hierarchy; therefore the script fails closed and must not broaden its target.

Never destroy arbitrary StyleLinks under CoreGui. Never treat disappearance of this warning as evidence that an avatar passed Avatar Setup, Studio playtest or UGC validation.

## Sources

- Roblox StyleLink API: https://create.roblox.com/docs/reference/engine/classes/StyleLink/StyleSheet
- Roblox UI styling: https://create.roblox.com/docs/ui/styling
- Roblox CoreGui API: https://create.roblox.com/docs/reference/engine/classes/CoreGui
- Studio bug report: https://devforum.roblox.com/t/multiple-stylelinks-warning-without-using-stylelinks/3953595
- Community reports of internal CoreGui warning: https://devforum.roblox.com/t/error-multiple-stylelinks-under-coregui-may-result-in-undefined-behaviour/3131055
