-- Temporary Studio-session workaround for Roblox's internal Avatar Previewer StyleLink conflict.
-- Run from Studio Command Bar BEFORE opening Avatar Setup.
-- It does not modify the place, GLB, rig, weights, UVs or textures.
-- It only disables the redundant AvatarCompatibilityPreviewer.Design StyleLink
-- directly under CoreGui.AvatarPreviewerEditingToolbar.Wrapper.Children.

local CoreGui = game:GetService("CoreGui")

local POLL_SECONDS = 0.25
local TARGET_TIMEOUT_SECONDS = 300
local TARGET_PARENT_SUFFIX = "AvatarPreviewerEditingToolbar.Wrapper.Children"
local KEEP_SHEET_SUFFIX = "StylingService.ViewportToolingFramework"
local DISABLE_SHEET_SUFFIX = "StylingService.AvatarCompatibilityPreviewer.Design"

local function endsWith(value, suffix)
	return value:sub(-#suffix) == suffix
end

local function fullNameOrNil(instance)
	return instance and instance:GetFullName() or "nil"
end

-- Stop a previous watcher created by this script.
if _G.AvatarPreviewerStyleLinkFixToken then
	_G.AvatarPreviewerStyleLinkFixToken.cancelled = true
end

local token = {
	cancelled = false,
	backups = {},
	fixedDebugIds = {},
}
_G.AvatarPreviewerStyleLinkFixToken = token

local function directStyleLinks(parent)
	local links = {}
	for _, child in ipairs(parent:GetChildren()) do
		if child:IsA("StyleLink") then
			table.insert(links, child)
		end
	end
	return links
end

local function classifyLink(link)
	local sheet = link.StyleSheet
	if not sheet then
		return "nil"
	end

	local name = sheet:GetFullName()
	if endsWith(name, KEEP_SHEET_SUFFIX) then
		return "keep"
	end
	if endsWith(name, DISABLE_SHEET_SUFFIX) then
		return "disable"
	end
	return "other"
end

local function findTargetParent()
	local toolbar = CoreGui:FindFirstChild("AvatarPreviewerEditingToolbar", true)
	if not toolbar then
		return nil
	end

	local wrapper = toolbar:FindFirstChild("Wrapper")
	if not wrapper then
		return nil
	end

	local children = wrapper:FindFirstChild("Children")
	if not children then
		return nil
	end

	if not endsWith(children:GetFullName(), TARGET_PARENT_SUFFIX) then
		return nil
	end

	return children
end

local function applyExactFix(parent)
	local keepLink = nil
	local disableLink = nil
	local links = directStyleLinks(parent)

	for _, link in ipairs(links) do
		local kind = classifyLink(link)
		if kind == "keep" then
			keepLink = link
		elseif kind == "disable" then
			disableLink = link
		end
	end

	-- Fail closed: only touch the exact known conflict.
	if not keepLink or not disableLink then
		return false
	end

	local debugId = disableLink:GetDebugId()
	if not token.backups[disableLink] then
		token.backups[disableLink] = disableLink.StyleSheet
	end

	if disableLink.StyleSheet ~= nil then
		disableLink.StyleSheet = nil
	end

	if not token.fixedDebugIds[debugId] then
		token.fixedDebugIds[debugId] = true
		print("Avatar Previewer StyleLink conflict corrected for this Studio session.")
		print("Parent:", parent:GetFullName())
		print("Kept:", keepLink:GetFullName(), "->", fullNameOrNil(keepLink.StyleSheet))
		print("Disabled temporarily:", disableLink:GetFullName(), "-> AvatarCompatibilityPreviewer.Design")
		print("Run _G.RestoreAvatarPreviewerStyleLinks() to undo.")
	end

	return true
end

_G.RestoreAvatarPreviewerStyleLinks = function()
	token.cancelled = true
	local restored = 0

	for link, originalSheet in pairs(token.backups) do
		if link and link.Parent and originalSheet then
			link.StyleSheet = originalSheet
			restored += 1
		end
	end

	print(string.format("Avatar Previewer StyleLinks restored: %d", restored))
end

_G.StopAvatarPreviewerStyleLinkFix = function()
	token.cancelled = true
	print("Avatar Previewer StyleLink watcher stopped. Existing temporary changes were not restored.")
end

task.spawn(function()
	local started = os.clock()
	local sawToolbar = false

	print("Avatar Previewer StyleLink watcher active.")
	print("Open Avatar Setup within 5 minutes; the exact internal duplicate will be corrected automatically.")

	while not token.cancelled and os.clock() - started < TARGET_TIMEOUT_SECONDS do
		local targetParent = findTargetParent()
		if targetParent then
			sawToolbar = true
			applyExactFix(targetParent)
		end
		task.wait(POLL_SECONDS)
	end

	if token.cancelled then
		return
	end

	if not sawToolbar then
		warn("AvatarPreviewerEditingToolbar was not opened within 5 minutes; no changes were made.")
	else
		print("Avatar Previewer StyleLink watcher finished after 5 minutes.")
	end
end)
