function initUi()
_G["fn0"] = function ()
 app.uiAction({["action"] = "ACTION_UNDO", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "UNDO", ["callback"] = "fn0", ["accelerator"] = "F1", }) 
_G["fn1"] = function ()
 app.uiAction({["action"] = "ACTION_REDO", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "REDO", ["callback"] = "fn1", ["accelerator"] = "F2", }) 
_G["fn2"] = function ()
 app.uiAction({["action"] = "ACTION_NEW_PAGE_AFTER", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "NEW_PAGE_AFTER", ["callback"] = "fn2", ["accelerator"] = "F3", }) 
_G["fn3"] = function ()
 app.changeCurrentPageBackground("plain")
end
app.registerUi({ ["menu"] = "plain", ["callback"] = "fn3", ["accelerator"] = "F5", }) 
_G["fn4"] = function ()
 app.changeCurrentPageBackground("ruled")
end
app.registerUi({ ["menu"] = "ruled", ["callback"] = "fn4", ["accelerator"] = "F6", }) 
_G["fn5"] = function ()
 app.changeCurrentPageBackground("graph")
end
app.registerUi({ ["menu"] = "graph", ["callback"] = "fn5", ["accelerator"] = "F7", }) 
_G["fn6"] = function ()
 app.changeCurrentPageBackground("dotted")
end
app.registerUi({ ["menu"] = "dotted", ["callback"] = "fn6", ["accelerator"] = "F8", }) 
_G["fn7"] = function ()
 app.changeCurrentPageBackground("lined")
end
app.registerUi({ ["menu"] = "lined", ["callback"] = "fn7", ["accelerator"] = "F9", }) 
_G["fn8"] = function ()
 app.changeToolColor({["color"] = 0x000000, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color black ", ["callback"] = "fn8", ["accelerator"] = "1", }) 
_G["fn9"] = function ()
 app.changeToolColor({["color"] = 0x008000, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color green ", ["callback"] = "fn9", ["accelerator"] = "2", }) 
_G["fn10"] = function ()
 app.changeToolColor({["color"] = 0x00c0ff, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color lightblue ", ["callback"] = "fn10", ["accelerator"] = "3", }) 
_G["fn11"] = function ()
 app.changeToolColor({["color"] = 0x00ff00, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color lightgreen", ["callback"] = "fn11", ["accelerator"] = "4", }) 
_G["fn12"] = function ()
 app.changeToolColor({["color"] = 0x3333cc, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color blue ", ["callback"] = "fn12", ["accelerator"] = "5", }) 
_G["fn13"] = function ()
 app.changeToolColor({["color"] = 0x808080, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color gray ", ["callback"] = "fn13", ["accelerator"] = "6", }) 
_G["fn14"] = function ()
 app.changeToolColor({["color"] = 0xff0000, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color red ", ["callback"] = "fn14", ["accelerator"] = "7", }) 
_G["fn15"] = function ()
 app.changeToolColor({["color"] = 0xff00ff, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color magenta ", ["callback"] = "fn15", ["accelerator"] = "8", }) 
_G["fn16"] = function ()
 app.changeToolColor({["color"] = 0xff8000, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color orange ", ["callback"] = "fn16", ["accelerator"] = "9", }) 
_G["fn17"] = function ()
 app.changeToolColor({["color"] = 0xffff00, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color yellow ", ["callback"] = "fn17", ["accelerator"] = "0", }) 
_G["fn18"] = function ()
 app.changeToolColor({["color"] = 0xffffff, ["selection"] = true})
end
app.registerUi({ ["menu"] = "color white ", ["callback"] = "fn18", ["accelerator"] = "minus", }) 
_G["fn19"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_PEN", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_PEN", ["callback"] = "fn19", ["accelerator"] = "Q", }) 
_G["fn20"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_ERASER", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_ERASER", ["callback"] = "fn20", ["accelerator"] = "W", }) 
_G["fn21"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_HIGHLIGHTER", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_HIGHLIGHTER", ["callback"] = "fn21", ["accelerator"] = "E", }) 
_G["fn22"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_HAND", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_HAND", ["callback"] = "fn22", ["accelerator"] = "R", }) 
_G["fn23"] = function ()
 app.uiAction({["action"] = "ACTION_TEX", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TEX", ["callback"] = "fn23", ["accelerator"] = "T", }) 
_G["fn24"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_VERTICAL_SPACE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_VERTICAL_SPACE", ["callback"] = "fn24", ["accelerator"] = "Y", }) 
_G["fn25"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_LINE_STYLE_PLAIN", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_LINE_STYLE_PLAIN", ["callback"] = "fn25", ["accelerator"] = "U", }) 
_G["fn26"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_LINE_STYLE_DASH", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_LINE_STYLE_DASH", ["callback"] = "fn26", ["accelerator"] = "I", }) 
_G["fn27"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_LINE_STYLE_DOT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_LINE_STYLE_DOT", ["callback"] = "fn27", ["accelerator"] = "O", }) 
_G["fn28"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_LINE_STYLE_DASH_DOT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_LINE_STYLE_DASH_DOT", ["callback"] = "fn28", ["accelerator"] = "P", }) 
_G["fn29"] = function ()
 app.uiAction({["action"] = "ACTION_RULER", ["enabled"] = false})
end
app.registerUi({ ["menu"] = "RULER", ["callback"] = "fn29", ["accelerator"] = "A", }) 
_G["fn30"] = function ()
 app.uiAction({["action"] = "ACTION_RULER", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "RULER", ["callback"] = "fn30", ["accelerator"] = "S", }) 
_G["fn31"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_DRAW_ARROW", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_DRAW_ARROW", ["callback"] = "fn31", ["accelerator"] = "D", }) 
_G["fn32"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_DRAW_RECT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_DRAW_RECT", ["callback"] = "fn32", ["accelerator"] = "F", }) 
_G["fn33"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_DRAW_ELLIPSE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_DRAW_ELLIPSE", ["callback"] = "fn33", ["accelerator"] = "G", }) 
_G["fn34"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_DRAW_COORDINATE_SYSTEM", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_DRAW_COORDINATE_SYSTEM", ["callback"] = "fn34", ["accelerator"] = "H", }) 
_G["fn35"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_DRAW_SPLINE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_DRAW_SPLINE", ["callback"] = "fn35", ["accelerator"] = "J", }) 
_G["fn36"] = function ()
 app.uiAction({["action"] = "ACTION_SHAPE_RECOGNIZER", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SHAPE_RECOGNIZER", ["callback"] = "fn36", ["accelerator"] = "K", }) 
_G["fn37"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_ERASER_STANDARD", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_ERASER_STANDARD", ["callback"] = "fn37", ["accelerator"] = "L", }) 
_G["fn38"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_ERASER_WHITEOUT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_ERASER_WHITEOUT", ["callback"] = "fn38", ["accelerator"] = "semicolon", }) 
_G["fn39"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_ERASER_DELETE_STROKE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_ERASER_DELETE_STROKE", ["callback"] = "fn39", ["accelerator"] = "apostrophe", }) 
_G["fn40"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_SELECT_OBJECT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_SELECT_OBJECT", ["callback"] = "fn40", ["accelerator"] = "Z", }) 
_G["fn41"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_SELECT_REGION", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_SELECT_REGION", ["callback"] = "fn41", ["accelerator"] = "X", }) 
_G["fn42"] = function ()
 app.uiAction({["action"] = "ACTION_TOOL_SELECT_RECT", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "TOOL_SELECT_RECT", ["callback"] = "fn42", ["accelerator"] = "C", }) 
_G["fn43"] = function ()
 app.uiAction({["action"] = "ACTION_SIZE_VERY_FINE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SIZE_VERY_FINE", ["callback"] = "fn43", ["accelerator"] = "V", }) 
_G["fn44"] = function ()
 app.uiAction({["action"] = "ACTION_SIZE_FINE", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SIZE_FINE", ["callback"] = "fn44", ["accelerator"] = "B", }) 
_G["fn45"] = function ()
 app.uiAction({["action"] = "ACTION_SIZE_MEDIUM", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SIZE_MEDIUM", ["callback"] = "fn45", ["accelerator"] = "N", }) 
_G["fn46"] = function ()
 app.uiAction({["action"] = "ACTION_SIZE_THICK", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SIZE_THICK", ["callback"] = "fn46", ["accelerator"] = "M", }) 
_G["fn47"] = function ()
 app.uiAction({["action"] = "ACTION_SIZE_VERY_THICK", ["enabled"] = true})
end
app.registerUi({ ["menu"] = "SIZE_VERY_THICK", ["callback"] = "fn47", ["accelerator"] = "comma", }) 

end


