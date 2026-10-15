-- Lesson components (docs/04 "Learner experience"): authors write fenced divs .quiz, .predict,
-- .parsons and .anim (see site/units/README.md); quiz.js, predict.js, parsons.js and anim.js make
-- them interactive. Fenced divs instead of shortcodes because Quarto shortcodes cannot take a body.
-- This filter validates the markup at build time and strips the multiple-choice answer key from
-- the visible HTML (pandoc would render "- [x]" as a checked checkbox).

local KINDS = { "quiz", "predict", "parsons", "anim" }
local BOX = { ["☐"] = false, ["☒"] = true } -- pandoc's task_lists markers

-- Quarto logs a Lua error() but still exits 0, so stop the render explicitly.
local function fail(msg)
  quarto.log.error("components.lua: " .. msg)
  os.exit(1)
end

-- Removes the task-list box from each option; returns the 0-based index of the "- [x]" option,
-- or nil if the list is not a task list.
local function strip_options(list, where)
  local answer
  for i, item in ipairs(list.content) do
    local first = item[1]
    local box = first and (first.t == "Plain" or first.t == "Para") and first.content[1]
    if not (box and box.t == "Str" and BOX[box.text] ~= nil) then
      if i > 1 then fail(where .. ": every option needs a [ ] or [x] box") end
      return nil
    end
    if BOX[box.text] then
      if answer then fail(where .. ": more than one option is marked [x]") end
      answer = i - 1
    end
    first.content:remove(1)
    if first.content[1] and first.content[1].t == "Space" then first.content:remove(1) end
  end
  if not answer then fail(where .. ": no option is marked [x]") end
  return answer
end

local function question(div, where)
  for _, block in ipairs(div.content) do
    if block.t == "BulletList" then
      local answer = strip_options(block, where)
      if answer then div.attributes.choice = tostring(answer) end
    end
  end
  if not div.attributes.choice and not div.attributes.answer then
    fail(where .. ": needs a task list with one [x] option or an answer=\"...\" attribute")
  end
  return div
end

local function count(div, pred)
  local n = 0
  div:walk({ CodeBlock = function(b) if pred(b) then n = n + 1 end end,
             Div = function(d) if pred(d) then n = n + 1 end end })
  return n
end

function Div(div)
  local kind
  for _, k in ipairs(KINDS) do
    if div.classes:includes(k) then kind = k end
  end
  if not kind then return nil end
  if div.identifier == "" then fail("a ." .. kind .. " div needs an id, e.g. {." .. kind .. " #u7-" .. kind .. "}") end
  local where = "." .. kind .. " #" .. div.identifier

  if kind == "quiz" then
    local n = 0
    div.content = div.content:walk({
      Div = function(d)
        if d.classes:includes("question") then
          n = n + 1
          return question(d, where .. " question " .. n)
        end
      end,
    })
    if n == 0 then fail(where .. ": needs at least one .question div") end
  elseif kind == "predict" then
    -- quarto-live may already have replaced the {pyodide} block by its cell div (filter order).
    local cells = count(div, function(b)
      return b.classes:includes("{pyodide}") or b.classes:includes("pyodide") or b.classes:includes("exercise-cell")
    end)
    if cells ~= 1 then fail(where .. ": needs exactly one {pyodide} block, found " .. cells) end
  elseif kind == "parsons" then
    local blocks = count(div, function(b) return b.t == "CodeBlock" and not b.classes:includes("distractor") end)
    if blocks ~= 1 then fail(where .. ": needs exactly one solution code block, found " .. blocks) end
  elseif kind == "anim" then
    if count(div, function(b) return b.t == "Div" and b.classes:includes("frame") end) < 2 then
      fail(where .. ": needs at least two .frame divs")
    end
  end
  return div
end
