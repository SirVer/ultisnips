-- Neovim on_bytes buffer change listener for UltiSnips.
--
-- Uses nvim_buf_attach to detect buffer changes.  The callback records
-- that a change happened; edit detection is done in Python by comparing
-- buffer snapshots.

local M = {}

vim.g._ultisnips_nvim_changes = {}
local suppressed = false

local function on_bytes(_, buf, _, start_row, start_col, _byte_offset,
                        old_end_row, old_end_col, _old_byte_length,
                        new_end_row, new_end_col, _new_byte_length)
  if suppressed then return end
  local changes = vim.g._ultisnips_nvim_changes
  table.insert(changes, {
    start_row, start_col,
    old_end_row, old_end_col,
    new_end_row, new_end_col,
  })
  vim.g._ultisnips_nvim_changes = changes
end

function M.attach(buf)
  M.detach()
  vim.api.nvim_buf_attach(buf, false, { on_bytes = on_bytes })
end

function M.detach()
  vim.g._ultisnips_nvim_changes = {}
end

function M.suppress()  suppressed = true end
function M.unsuppress() suppressed = false end
function M.reset()     vim.g._ultisnips_nvim_changes = {} end

return M
