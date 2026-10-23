-- Phase 0 oracle run: boot, attract and a short scripted game in MAME, with screenshots, the P2
-- bank register writes (0x2FFFF0-0x2FFFFF) and the Z80's NEO-ZMC bank ports (0x08-0x0B).
--
-- Environment variables:
--   PD_OUT                 output folder (Windows path): banks.txt, z80_banks.txt, screenshots
--                          as snap_NNNNNN.png in -snapshot_directory
--   PD_SCREENSHOT_FRAMES   comma-separated frame numbers
--   PD_PLAY=1              coin, START, the first soldier, then right + fire (A) + jump (B) now
--                          and then
--   PD_DEVMODE=1           BIOS development mode: 0x10FE80 read as 1 by cartridge code
--   PD_DIPS=hex            debug dips: the word 0x10F000 read with these bits set by cartridge code

if pd_oracle_loaded then return end       -- MAME reruns the autoboot script after a soft reset
pd_oracle_loaded = true

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local z80 = manager.machine.devices[":audiocpu"]
local scr = manager.machine.screens[":screen"]
local out = os.getenv("PD_OUT") or "."

-- ---- P2 bank register
local banks = { total = 0, values = {}, pcs = {}, first = {} }
oracle_btap = mem:install_write_tap(0x2FFFF0, 0x2FFFFF, "pd_bank_w", function(offset, data, mask)
    local pc = cpu.state["PC"].value
    banks.total = banks.total + 1
    local key = string.format("%06X %04X %04X", offset, data, mask)
    banks.values[key] = (banks.values[key] or 0) + 1
    banks.pcs[pc] = (banks.pcs[pc] or 0) + 1
    if #banks.first < 60 then
        banks.first[#banks.first + 1] = string.format("frame=%d pc=%06X addr=%06X data=%04X mask=%04X",
            scr:frame_number(), pc, offset, data, mask)
    end
end)

-- ---- Z80 bank ports
local zb = {}
oracle_ztap = z80.spaces["io"]:install_read_tap(0x0000, 0xFFFF, "pd_z80_bank", function(offset, data, mask)
    local low = offset & 0xFF
    if low < 0x08 or low > 0x0B then return end
    local key = string.format("%02X %02X", low, offset >> 8)
    zb[key] = (zb[key] or 0) + 1
end)

-- ---- developer mode and debug dips, as the port's PD_DEVMODE / PD_DIPS (cartridge code only)
if os.getenv("PD_DEVMODE") == "1" then
    oracle_dev = mem:install_read_tap(0x10FE80, 0x10FE81, "pd_dev", function(offset, data, mask)
        if cpu.state["PC"].value < 0xC00000 then
            if mask & 0xFF00 ~= 0 then return (data & 0x00FF) | 0x0100 end
        end
    end)
end
local dips = tonumber(os.getenv("PD_DIPS") or "", 16)
if dips then
    oracle_dips = mem:install_read_tap(0x10F000, 0x10F001, "pd_dips", function(offset, data, mask)
        if cpu.state["PC"].value < 0xC00000 then return data | (dips & mask) end
    end)
end

-- ---- inputs and screenshots
local fields = {}
for _, port in pairs(manager.machine.ioport.ports) do
    for name, field in pairs(port.fields) do fields[name] = field end
end
local shots = {}
for n in string.gmatch(os.getenv("PD_SCREENSHOT_FRAMES") or "", "%d+") do shots[tonumber(n)] = true end
local play = os.getenv("PD_PLAY") == "1"
local held = {}
local function press(name, on)
    local f = fields[name]
    if f then f:set_value(on and 1 or 0) end
end
oracle_frame = emu.add_machine_frame_notifier(function()
    local f = scr:frame_number()
    if shots[f] then scr:snapshot(string.format("snap_%06d.png", f)) end
    if not play then return end
    local want = {}
    if f >= 1200 and f < 1206 then want["Coin 1"] = true end
    for _, s in ipairs({ 1400, 1700, 2000, 2300, 2600, 2900 }) do
        if f >= s and f < s + 6 then want["1 Player Start"] = true end
    end
    for _, s in ipairs({ 1800, 2100, 2400, 2700, 3000, 3300 }) do
        if f >= s and f < s + 6 then want["P1 A"] = true end
    end
    if f >= 3400 then
        want["P1 Right"] = (f % 240) < 200
        want["P1 A"] = (f % 8) < 4
        want["P1 B"] = (f % 90) < 6
        want["P1 C"] = (f % 600) < 4
    end
    for _, n in ipairs({ "Coin 1", "1 Player Start", "P1 A", "P1 B", "P1 C", "P1 Right" }) do
        local on = want[n] or false
        if held[n] ~= on then press(n, on); held[n] = on end
    end
end)

oracle_stop = emu.add_machine_stop_notifier(function()
    local f = assert(io.open(out .. "\\banks.txt", "w"))
    f:write(string.format("bank writes: %d\n", banks.total))
    for k, n in pairs(banks.values) do f:write(string.format("value %s: %d\n", k, n)) end
    for pc, n in pairs(banks.pcs) do f:write(string.format("pc %06X: %d\n", pc, n)) end
    for _, s in ipairs(banks.first) do f:write(s .. "\n") end
    f:close()
    f = assert(io.open(out .. "\\z80_banks.txt", "w"))
    for k, n in pairs(zb) do f:write(string.format("%s %d\n", k, n)) end
    f:close()
end)
