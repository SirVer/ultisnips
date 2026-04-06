-- Neovim on_bytes buffer change listener for UltiSnips.
--
-- Uses nvim_buf_attach to detect buffer changes.  The on_bytes callback
-- simply records that a change happened; the actual edit detection is
-- done in Python by comparing old vs new buffer state.

local M = {}

vim.g._ultisnips_nvim_changes = {}

local attached_buf = nil
local suppressed = false

local function on_bytes(_, buf, _, start_row, start_col, _byte_offset,
                        old_end_row, old_end_col, _old_byte_length,
                        new_end_row, new_end_col, _new_byte_length)
  if suppressed then
    return
  end

  -- Just record that a change happened.  Python will compare buffer
  -- snapshots to determine the actual edit.
  local changes = vim.g._ultisnips_nvim_changes
  table.insert(changes, 1)
  vim.g._ultisnips_nvim_changes = changes
end

function M.attach(buf)
  M.detach()
  vim.api.nvim_buf_attach(buf, false, {
    on_bytes = on_bytes,
  })
  attached_buf = buf
end

function M.detach()
  attached_buf = nil
  vim.g._ultisnips_nvim_changes = {}
end

function M.suppress()
  suppressed = true
end

function M.unsuppress()
  suppressed = false
end

function M.reset()
  vim.g._ultisnips_nvim_changes = {}
end

return M
