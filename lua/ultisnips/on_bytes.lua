-- Neovim on_bytes buffer change listener for UltiSnips.
--
-- Uses nvim_buf_attach with on_bytes to capture exact byte coordinates
-- for every buffer change.  Events are appended to vim.g._ultisnips_nvim_changes
-- (cleared by the Python side after consumption).

local M = {}

vim.g._ultisnips_nvim_changes = {}
local suppressed = false
-- Each attach bumps this token. Active callback closes over its token;
-- when a new attach replaces it, the old callback returns true on its
-- next firing to detach itself. nvim_buf_attach has no per-callback
-- removal API, so this is how we avoid stacking callbacks.
local attached_token = 0

local function make_callback(token)
  return function(_, _buf, _, start_row, start_col, _byte_offset,
                  old_end_row, old_end_col, _old_byte_length,
                  new_end_row, new_end_col, _new_byte_length)
    if token ~= attached_token then return true end
    if suppressed then return end
    local changes = vim.g._ultisnips_nvim_changes
    table.insert(changes, {
      start_row, start_col,
      old_end_row, old_end_col,
      new_end_row, new_end_col,
    })
    vim.g._ultisnips_nvim_changes = changes
  end
end

function M.attach(buf)
  M.detach()
  attached_token = attached_token + 1
  vim.api.nvim_buf_attach(buf, false, { on_bytes = make_callback(attached_token) })
end

function M.detach()
  attached_token = attached_token + 1
  vim.g._ultisnips_nvim_changes = {}
end

function M.suppress()  suppressed = true end
function M.unsuppress() suppressed = false end
function M.reset()     vim.g._ultisnips_nvim_changes = {} end

return M
