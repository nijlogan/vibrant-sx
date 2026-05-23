import os
import re
import itertools

DEBOUNCE_TIME = 1.0

ENGINE_SHORTHANDS = {
    "p3": "ph3",
    "sx": "ph3sx",
    "zl": "zlabel",
    # insert more languages here as needed
    "vb": "vibrant-sx"
}

ENGINE_LANGUAGES = list(ENGINE_SHORTHANDS)

ENGINE_NON_FUNCTIONS = [
    { "sig": "doc", "lang": "vb", "kind": 8, "completion": "/***\n$0\n***/" },
    { "sig": "ext", "lang": "vb", "kind": 8, "completion": "//// external dependency" },
    { "sig": "friend", "lang": "vb", "kind": 8, "completion": "//// friend \"./path.dnh\"" },

    { "sig": "local", "lang": "p3 sx zl", "kind": 1, "completion": "local\n{\n\t$0\n}" },
    { "sig": "function", "lang": "p3 sx zl", "kind": 1, "completion": "function Fun()\n{\n\t$0\n}" },
    { "sig": "function", "lang": "sx zl", "kind": 1, "completion": "function<void> Fun()\n{\n\t$0\n}", "desc": "function<return-type>" },
    { "sig": "func", "lang": "zl", "kind": 1, "completion": "func Fun()\n{\n\t$0\n}" },
    { "sig": "func", "lang": "zl", "kind": 1, "completion": "func<void> Fun()\n{\n\t$0\n}", "desc": "func<return-type>" },
    { "sig": "sub", "lang": "p3 sx zl", "kind": 1, "completion": "sub Sub()\n{\n\t$0\n}" },
    { "sig": "task", "lang": "p3 sx zl", "kind": 1, "completion": "task _Task()\n{\n\t$0\n}" },
    { "sig": "async", "lang": "sx zl", "kind": 1, "completion": "async\n{\n\t$0\n}" },
    { "sig": "fcall", "lang": "zl", "kind": 1, "completion": "fcall Callback()\n{\n\t$0\n}" },
    { "sig": "tcall", "lang": "zl", "kind": 1, "completion": "tcall _Callback()\n{\n\t$0\n}" },

    { "sig": "true", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "false", "lang": "p3 sx zl", "kind": 1 },

    { "sig": "case", "lang": "p3 sx zl", "kind": 1, "completion": "case (/*value*/)\n{\n\t$0\n}" },
    { "sig": "others", "lang": "p3 sx zl", "kind": 1, "completion": "others\n{\n\t$0\n}" },
    { "sig": "do", "lang": "p3 sx zl", "kind": 1, "completion": "do\n{\n\t$0\n} while (/*cond*/);" },
    { "sig": "else", "lang": "p3 sx zl", "kind": 1, "completion": "else\n{\n\t$0\n}" },
    { "sig": "for", "lang": "sx zl", "kind": 1, "completion": "for (int i = 0; i < /*n*/; i++)\n{\n\t$0\n}", "desc": "Standard for-loop: for (int i = 0; i < n; i++)" },
    { "sig": "for", "lang": "sx zl", "kind": 1, "completion": "for each (var item in ref /*arr*/)\n{\n\t$0\n}", "desc": "Standard for-each-loop: for each (var item in ref arr)" },
    { "sig": "for", "lang": "sx zl", "kind": 1, "completion": "for each ((int index, var item) in ref /*arr*/)\n{\n\t$0\n}", "desc": "Enumerating for-each-loop: for each ((int index, var item) in ref arr)" },
    { "sig": "each", "lang": "sx zl", "kind": 1, "completion": "each (var item in ref /*arr*/)\n{\n\t$0\n}", "desc": "Standard for-each-loop: for each (var item in ref arr)" },
    { "sig": "each", "lang": "sx zl", "kind": 1, "completion": "each ((int index, var item) in ref /*arr*/)\n{\n\t$0\n}", "desc": "Enumerating for-each-loop: for each ((int index, var item) in ref arr)" },
    { "sig": "in", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "ref", "lang": "sx zl", "kind": 1 },
    { "sig": "ascent", "lang": "p3 sx zl", "kind": 1, "completion": "ascent (i in 0../*n*/)\n{\n\t$0\n}" },
    { "sig": "ascent", "lang": "sx zl", "kind": 1, "completion": "ascent (int i in 0../*n*/)\n{\n\t$0\n}" },
    { "sig": "descent", "lang": "p3 sx zl", "kind": 1, "completion": "descent (i in 0../*n*/)\n{\n\t$0\n}" },
    { "sig": "descent", "lang": "sx zl", "kind": 1, "completion": "descent (int i in 0../*n*/)\n{\n\t$0\n}" },
    { "sig": "loop", "lang": "p3 sx zl", "kind": 1, "completion": "loop\n{\n\t$0\n}", "desc": "loop (Infinite loop)" },
    { "sig": "loop", "lang": "p3 sx zl", "kind": 1, "completion": "loop (/*n*/)\n{\n\t$0\n}", "desc": "loop (n) (Finite loop)" },
    { "sig": "if", "lang": "p3 sx zl", "kind": 1, "completion": "if (/*cond*/)\n{\n\t$0\n}" },
    { "sig": "alternative", "lang": "sx zl", "kind": 1, "completion": "alternative (/*state*/)\n\ncase (/*value*/)\n{\n\t$0\n}\n\nothers\n{\n\t\n}" },
    { "sig": "while", "lang": "p3 sx zl", "kind": 1, "completion": "while (/*cond*/)\n{\n\t$0\n}" },
    { "sig": "times", "lang": "p3 sx zl", "kind": 1, "completion": "times (/*n*/)\n{\n\t$0\n}" },

    { "sig": "return", "lang": "p3 sx zl", "kind": 1, "completion": "return;" },
    { "sig": "continue", "lang": "sx zl", "kind": 1, "completion": "continue;" },
    { "sig": "break", "lang": "p3 sx zl", "kind": 1, "completion": "break;" },

    { "sig": "yield", "lang": "p3 sx zl", "kind": 1, "completion": "yield;" },

    { "sig": "bool", "lang": "sx zl", "kind": 2 },
    { "sig": "char", "lang": "sx zl", "kind": 2 },
    { "sig": "float", "lang": "sx zl", "kind": 2 },
    { "sig": "string", "lang": "sx zl", "kind": 2 },
    { "sig": "int", "lang": "sx zl", "kind": 2 },
    { "sig": "object", "lang": "zl", "kind": 2, "desc": "For objects, to mark them as distinct from int." },
    { "sig": "ptr", "lang": "zl", "kind": 2, "desc": "For map pointers (common data, shaders...), to mark them as distinct from int." },
    { "sig": "fn", "lang": "zl", "kind": 2, "desc": "For function pointers (function, task, sub, fcall, tcall), to mark them as distinct from int." },
    { "sig": "tenv", "lang": "zl", "kind": 2, "desc": "For task return value, which is the task's environment, to mark it as distinct from int." },
    { "sig": "var", "lang": "p3 sx zl", "kind": 2 },
    { "sig": "let", "lang": "p3 sx zl", "kind": 2 },
    { "sig": "real", "lang": "p3", "kind": 2, "desc": "Only available in ph3. Removed as of ph3sx." },
    { "sig": "const", "lang": "sx zl", "kind": 2 },
    { "sig": "void", "lang": "sx zl", "kind": 2 },

    { "sig": "@Loading", "lang": "p3 sx zl", "kind": 4, "completion": "@Loading\n{\n\t$0\n}" },
    { "sig": "@Initialize", "lang": "p3 sx zl", "kind": 4, "completion": "@Initialize\n{\n\t$0\n}" },
    { "sig": "@Event", "lang": "p3 sx zl", "kind": 4, "completion": "@Event\n{\n\talternative (GetEventType())\n\n\tcase (EV_USER)\n\t{\n\t\t$0\n\t}\n}" },
    { "sig": "@MainLoop", "lang": "p3 sx zl", "kind": 4, "completion": "@MainLoop\n{\n\t$0\n\n\tyield;\n}" },
    { "sig": "@Finalize", "lang": "p3 sx zl", "kind": 4, "completion": "@Finalize\n{\n\t$0\n}" },

    { "sig": "#ScriptVersion", "lang": "p3 sx zl", "kind": 6, "completion": "#ScriptVersion[3]" },
    { "sig": "#TouhouDanmakufu", "lang": "p3 sx zl", "kind": 6, "completion": "#TouhouDanmakufu[/*Single/Plural/Stage/Player/Package*/]" },
    { "sig": "#Title", "lang": "p3 sx zl", "kind": 6, "completion": "#Title[\"text\"]" },
    { "sig": "#Text", "lang": "p3 sx zl", "kind": 6, "completion": "#Text[\"text\"]" },
    { "sig": "#Image", "lang": "p3 sx zl", "kind": 6, "completion": "#Image[\"./path.ext\"]" },
    { "sig": "#Player", "lang": "p3 sx zl", "kind": 6, "completion": "#Player[\"./path1.dnh\", \"./path2.dnh\"...]" },
    { "sig": "#ID", "lang": "p3 sx zl", "kind": 6, "completion": "#ID[\"text\"]" },
    { "sig": "#ReplayName", "lang": "p3 sx zl", "kind": 6, "completion": "#ReplayName[\"text\"]" },
    { "sig": "#System", "lang": "p3 sx zl", "kind": 6, "completion": "#System[\"./path.dnh\"]" },
    { "sig": "#Title", "lang": "p3 sx zl", "kind": 6, "completion": "#Title[\"Name\"]" },

    { "sig": "#include", "lang": "p3 sx zl", "kind": 5, "completion": "#include \"./path.dnh\"" },

    # { "sig": "#if", "lang": "sx zl", "kind": 6, "completion": "#if cond\n\n\t$0\n\n#elif cond\n\n\t\n\n#else\n\n\t\n\n#endif" },
    { "sig": "#ifdef", "lang": "sx zl", "kind": 6, "completion": "#ifdef macro /* one of _DNH_PH3SX_ / _DNH_PH3SX_ZLABEL_ / SCRIPT_STAGE / SCRIPT_PACKAGE */\n\n\t$0\n\n#else\n\n\t\n\n#endif" },
    { "sig": "#ifndef", "lang": "sx zl", "kind": 6, "completion": "#ifndef macro /* one of _DNH_PH3SX_ / _DNH_PH3SX_ZLABEL_ / SCRIPT_STAGE / SCRIPT_PACKAGE */\n\n\t$0\n\n#else\n\n\t\n\n#endif" },
    # { "sig": "#elif", "lang": "sx zl", "kind": 6, "completion": "#elif cond\n\n\t" },
    { "sig": "#else", "lang": "sx zl", "kind": 6, "completion": "#else\n\n\t" },
    { "sig": "#endif", "lang": "sx zl", "kind": 6 },

    { "sig": "#UserShotData", "lang": "p3 sx zl", "kind": 6 },
    { "sig": "#UserItemData", "lang": "p3 sx zl", "kind": 6 },

    { "sig": "Single", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "Plural", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "Stage", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "Player", "lang": "p3 sx zl", "kind": 1 },
    { "sig": "Package", "lang": "p3 sx zl", "kind": 1 },

    # Constants

    { "sig": "_DNH_PH3SX_", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "_DNH_PH3SX_ZLABEL_", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "SCRIPT_STAGE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "SCRIPT_PACKAGE", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "KEY_INVALID", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "-1" },
    { "sig": "VK_LEFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_RIGHT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_UP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_SHOT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_BOMB", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_SLOWMOVE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_USER1", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_USER2", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_OK", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_CANCEL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_PAUSE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_USER_ID_STAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "VK_USER_ID_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "STATUS_INVALID", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATUS_LOADED", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATUS_LOADING", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATUS_RUNNING", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATUS_PAUSED", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATUS_CLOSING", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "STAGE_STATE_FINISHED", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "STAGE_RESULT_BREAK_OFF", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STAGE_RESULT_PLAYER_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STAGE_RESULT_CLEARED", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "NULL", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "0" },

    { "sig": "INF", "lang": "sx zl", "type": "const int", "kind": 7, "value": "infinity float" },
    { "sig": "NAN", "lang": "sx zl", "type": "const int", "kind": 7, "value": "NaN float" },

    { "sig": "FLOAT_TYPE_SUBNORMAL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FLOAT_TYPE_NORMAL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FLOAT_TYPE_ZERO", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FLOAT_TYPE_INFINITY", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FLOAT_TYPE_NAN", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "VAR_INT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "VAR_FLOAT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "VAR_CHAR", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "VAR_BOOL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "VAR_ARRAY", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "VAR_STRING", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "LERP_LINEAR", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_SMOOTH", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_SMOOTHER", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_ACCELERATE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_DECELERATE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_RUBBERBAND", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "LERP_BELL", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "M_PI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "3.14159265358979323846" },
    { "sig": "M_PI_2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.57079632679489661923" },
    { "sig": "M_PI_4", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.78539816339744830962" },
    { "sig": "M_PI_X2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "6.28318530717958647693" },
    { "sig": "M_PI_X4", "lang": "sx zl", "type": "const float", "kind": 7, "value": "12.5663706143591729539" },
    { "sig": "M_1_PI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.31830988618379067154" },
    { "sig": "M_2_PI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.63661977236758134308" },
    { "sig": "M_SQRTPI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.772453850905516027298" },
    { "sig": "M_1_SQRTPI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.56418958354775628695" },
    { "sig": "M_2_SQRTPI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.128379167095512573896" },
    { "sig": "M_SQRT2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.4142135623730950488" },
    { "sig": "M_SQRT2_2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.7071067811865475244" },
    { "sig": "M_SQRT2_X2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "2.8284271247461900976" },
    { "sig": "M_E", "lang": "sx zl", "type": "const float", "kind": 7, "value": "2.71828182845904523536" },
    { "sig": "M_LOG2E", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.44269504088896340736" },
    { "sig": "M_LOG10E", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.43429448190325182765" },
    { "sig": "M_LN2", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.69314718055994530942" },
    { "sig": "M_LN10", "lang": "sx zl", "type": "const float", "kind": 7, "value": "2.30258509299404568402" },
    { "sig": "M_PHI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "1.61803398874989484821" },
    { "sig": "M_1_PHI", "lang": "sx zl", "type": "const float", "kind": 7, "value": "0.6180339887498948482" },

    { "sig": "ID_INVALID", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "-1" },
    { "sig": "OBJ_BASE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_PRIMITIVE_2D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPRITE_2D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPRITE_LIST_2D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_PRIMITIVE_3D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPRITE_3D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_TRAJECTORY_3D", "lang": "p3 sx zl", "type": "const int", "kind": 7, "desc": "Only available in ph3 and ph3sx. Removed as of ph3sx-zlabel." },
    { "sig": "OBJ_PARTICLE_LIST_2D", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_PARTICLE_LIST_3D", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SHADER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_MESH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_TEXT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SOUND", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_FILE_TEXT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_FILE_BINARY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "COLOR_PERMUTE_ARGB", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_RGBA", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_BGRA", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_RGB", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_BGR", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_A", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_R", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_G", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "COLOR_PERMUTE_B", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "BLEND_NONE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_ALPHA", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_ADD_RGB", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_ADD_ARGB", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_MULTIPLY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_SUBTRACT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_SHADOW", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_INV_DESTRGB", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BLEND_ALPHA_INV", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "CULL_NONE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CULL_CW", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CULL_CCW", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "IFF_BMP", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "IFF_JPG", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "IFF_TGA", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "IFF_PNG", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "IFF_DDS", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "IFF_PPM", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "FILTER_NONE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FILTER_POINT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FILTER_LINEAR", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "FILTER_ANISOTROPIC", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "CAMERA_NORMAL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CAMERA_LOOKAT", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "PRIMITIVE_POINT_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "PRIMITIVE_LINELIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "PRIMITIVE_LINESTRIP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "PRIMITIVE_TRIANGLELIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "PRIMITIVE_TRIANGLESTRIP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "PRIMITIVE_TRIANGLEFAN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "BORDER_NONE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BORDER_FULL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "BORDER_SHADOW", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "ALIGNMENT_LEFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ALIGNMENT_RIGHT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ALIGNMENT_CENTER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ALIGNMENT_TOP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ALIGNMENT_BOTTOM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "CHARSET_ANSI", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_DEFAULT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_SHIFTJIS", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_HANGUL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_JOHAB", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_CHINESEBIG5", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_TURKISH", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_VIETNAMESE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_HEBREW", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_ARABIC", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "CHARSET_THAI", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "SOUND_BGM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "SOUND_SE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "SOUND_VOICE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "SOUND_UNKNOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "SOUND_WAVE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "SOUND_OGG", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_FORMAT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_CHANNEL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SAMPLE_RATE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_AVG_BYTE_PER_SEC", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_BLOCK_ALIGN", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_BIT_PER_SAMPLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_POSITION", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_POSITION_SAMPLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_LENGTH", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_LENGTH_SAMPLE", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "CODE_ACP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "CODE_UTF8", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "CODE_UTF16LE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "CODE_UTF16BE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "ENDIAN_LITTLE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ENDIAN_BIG", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "KEY_FREE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_PUSH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_PULL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_HOLD", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "MOUSE_LEFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOUSE_RIGHT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOUSE_MIDDLE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "KEY_ESCAPE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_1", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_2", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_3", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_4", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_5", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_6", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_7", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_8", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_9", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_0", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_MINUS", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_EQUALS", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_BACK", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_TAB", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_Q", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_W", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_E", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_R", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_T", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_Y", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_U", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_I", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_O", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_P", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LBRACKET", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RBRACKET", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RETURN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LCONTROL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_A", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_S", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_D", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_G", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_H", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_J", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_K", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_L", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SEMICOLON", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_APOSTROPHE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_GRAVE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LSHIFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_BACKSLASH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_Z", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_X", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_C", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_V", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_B", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_N", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_M", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_COMMA", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_PERIOD", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SLASH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RSHIFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_MULTIPLY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LMENU", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SPACE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_CAPITAL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F1", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F2", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F3", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F4", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F5", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F6", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F7", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F8", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F9", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F10", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMLOCK", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SCROLL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD7", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD8", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD9", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SUBTRACT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD4", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD5", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD6", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_ADD", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD1", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD2", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD3", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPAD0", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_DECIMAL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F11", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F12", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F13", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F14", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_F15", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_KANA", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_CONVERT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NOCONVERT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_YEN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPADEQUALS", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_CIRCUMFLEX", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_AT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_COLON", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_UNDERLINE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_KANJI", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_STOP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_AX", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_UNLABELED", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPADENTER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RCONTROL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NUMPADCOMMA", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_DIVIDE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SYSRQ", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RMENU", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_PAUSE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_HOME", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_UP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_PRIOR", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LEFT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RIGHT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_END", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_NEXT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_INSERT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_DELETE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_LWIN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_RWIN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_APPS", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_POWER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "KEY_SLEEP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_USER_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "100000" },
    { "sig": "EV_USER", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "1000000" },
    { "sig": "EV_USER_SYSTEM", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "2000000" },
    { "sig": "EV_USER_STAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "3000000" },
    { "sig": "EV_USER_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "4000000" },
    { "sig": "EV_USER_PACKAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7, "value": "5000000" },

    { "sig": "EV_APP_LOSE_FOCUS", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_APP_RESTORE_FOCUS", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "TYPE_SCRIPT_ALL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SCRIPT_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SCRIPT_SINGLE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SCRIPT_PLURAL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SCRIPT_STAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SCRIPT_PACKAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_SCRIPT_TYPE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_PATH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_ID", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_TITLE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_TEXT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_IMAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SCRIPT_REPLAY_NAME", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "REPLAY_FILE_PATH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_DATE_TIME", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_USER_NAME", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_TOTAL_SCORE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_FPS_AVERAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_PLAYER_NAME", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_STAGE_INDEX_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_STAGE_START_SCORE_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_STAGE_LAST_SCORE_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_COMMENT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "REPLAY_INDEX_ACTIVE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_INDEX_DIGIT_MIN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_INDEX_DIGIT_MAX", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "REPLAY_INDEX_USER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "RESULT_CANCEL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "RESULT_END", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "RESULT_RETRY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "RESULT_SAVE_REPLAY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "TYPE_ALL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_SHOT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_CHILD", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_IMMEDIATE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_FADE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TYPE_ITEM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "OWNER_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OWNER_ENEMY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "DELAY_DEFAULT", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "DELAY_LERP", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "PATTERN_FAN", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_FAN_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_RING", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_RING_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_WAVE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_WAVE_AIMED", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ARROW", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ARROW_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_POLYGON", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_POLYGON_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_AMORPHOUS", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_AMORPHOUS_AIMED", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ELLIPSE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ELLIPSE_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_SCATTER_ANGLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_SCATTER_SPEED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_SCATTER", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_LINE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_LINE_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ROSE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_ROSE_AIMED", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "PATTERN_BASEPOINT_RESET", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "TRANSFORM_WAIT", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADD_SPEED_ANGLE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ANGULAR_MOVE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_N_DECEL_CHANGE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_GRAPHIC_CHANGE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_BLEND_CHANGE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_TO_SPEED_ANGLE", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_A1", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_A2", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_B1", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_B2", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_C1", "lang": "sx", "type": "const int", "kind": 7 },
    { "sig": "TRANSFORM_ADDPATTERN_C2", "lang": "sx", "type": "const int", "kind": 7 },

    { "sig": "STATE_NORMAL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATE_HIT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATE_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "STATE_END", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "ITEM_1UP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_1UP_S", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_SPELL_S", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_POWER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_POWER_S", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_POINT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_POINT_S", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_USER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "ITEM_AUTOCOLLECT_PLAYER_SCOPE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_AUTOCOLLECT_COLLECT_ALL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_AUTOCOLLECT_POC_LINE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_AUTOCOLLECT_COLLECT_CIRCLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_AUTOCOLLECT_ALL", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "ITEM_MOVE_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_MOVE_TOPLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "ITEM_MOVE_SCORE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "OBJ_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPELL_MANAGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_ENEMY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_ENEMY_BOSS", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_ENEMY_BOSS_SCENE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SHOT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_LOOSE_LASER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_STRAIGHT_LASER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_CURVE_LASER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SHOT_PATTERN", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_ITEM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_LIFE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_DAMAGE_RATE_SHOT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_DAMAGE_RATE_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SHOT_HIT_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_DAMAGE_PREVIOUS_FRAME", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_TIMER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_TIMERF", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ORGTIMERF", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_LAST_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_DURABLE_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_REQUIRE_ALL_DOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_SPELL_SCORE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_REMAIN_STEP_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ACTIVE_STEP_LIFE_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ACTIVE_STEP_TOTAL_MAX_LIFE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ACTIVE_STEP_TOTAL_LIFE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ACTIVE_STEP_LIFE_RATE_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_LAST_STEP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_PLAYER_SHOOTDOWN_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_PLAYER_SPELL_COUNT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_CURRENT_LIFE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_CURRENT_LIFE_MAX", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_ITEM_SCORE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ITEM_MOVE_TYPE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_ITEM_TYPE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "INFO_EXISTS", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_PATH", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_RECT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_DELAY_COLOR", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_BLEND", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_COLLISION", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_COLLISION_LIST", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "INFO_IS_FIXED_ANGLE", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_REQUEST_LIFE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_TIMER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_IS_SPELL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_IS_LAST_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_IS_DURABLE_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_REQUIRE_ALL_DOWN", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_SPELL_SCORE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_REQUEST_REPLAY_TARGET_COMMON_AREA", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_GET_ITEM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_COLLECT_ITEM", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_CANCEL_ITEM", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_DELETE_SHOT_IMMEDIATE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_DELETE_SHOT_TO_ITEM", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_DELETE_SHOT_FADE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_GRAZE", "lang": "p3 sx zl", "type": "const int", "kind": 7, "desc": "In ph3sx and ph3sx-zlabel, this is called in a separate thread. Using rand() here WILL cause replay desyncs." },
    { "sig": "EV_HIT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_DELETE_SHOT_PLAYER", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_TIMEOUT", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_START_BOSS_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_END_BOSS_SPELL", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_GAIN_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_START_BOSS_STEP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_END_BOSS_STEP", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_PLAYER_SHOOTDOWN", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_PLAYER_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_PLAYER_REBIRTH", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "REBIRTH_DEFAULT", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_PAUSE_ENTER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "EV_PAUSE_LEAVE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "EV_REQUEST_SPELL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "TARGET_ALL", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TARGET_ENEMY", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "TARGET_PLAYER", "lang": "p3 sx zl", "type": "const int", "kind": 7 },

    { "sig": "MOVE_OTHER", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_NONE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_ANGLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_XY", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_XY_ANGLE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_LINE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_CURVE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_SPLINE", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "MOVE_LINE_SPEED", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_LINE_FRAME", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_LINE_WEIGHT", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "MOVE_CURVE_QUADRATIC_BEZIER", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_CURVE_CUBIC_BEZIER", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "MOVE_CURVE_HERMITE", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "TOPLAYER_CHANGE", "lang": "sx zl", "type": "const int", "kind": 7 },
    { "sig": "NO_CHANGE", "lang": "p3 sx zl", "type": "const int", "kind": 7 },
    { "sig": "UNCAPPED_MAX", "lang": "sx zl", "type": "const int", "kind": 7 },

    { "sig": "OBJ_SPLINE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "OBJ_SPRING_MASS_SYSTEM", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "ANGLE_FIXED", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ANGLE_ROTATE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ANGLE_CENTER", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ANGLE_FOLLOW", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ANGLE_ABSOLUTE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ANGLE_RELATIVE", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "ORDER_ANGLE_SCALE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "ORDER_SCALE_ANGLE", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "LOOP_FORWARD", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "LOOP_BACKWARD", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "LOOP_FORWARD_BACKWARD", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "LOOP_BACKWARD_FORWARD", "lang": "zl", "type": "const int", "kind": 7 },

    { "sig": "SHOTANIM_NONE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "SHOTANIM_JIGGLE", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "SHOTANIM_SQUISH", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "SHOTANIM_FLUTTER", "lang": "zl", "type": "const int", "kind": 7 },
    { "sig": "SHOTANIM_DANCE", "lang": "zl", "type": "const int", "kind": 7 },
]

ENGINE_SIGS = [non_func["sig"] for non_func in ENGINE_NON_FUNCTIONS]

ENGINE_VARIABLE_SIGS = [non_func["sig"] for non_func in ENGINE_NON_FUNCTIONS if non_func["kind"] == 7]

ENGINE_AT_SIGS = [non_func["sig"] for non_func in ENGINE_NON_FUNCTIONS if non_func["kind"] == 4]

VIBRANT_SX_SIGS = [non_func["sig"] for non_func in ENGINE_NON_FUNCTIONS if non_func["lang"] == "vb"]

ENGINE_TRIGGERS = [
    {
        "trigger": entry["sig"],
        "language": entry["lang"],
        "type": entry["type"],
        "value": "<span style=\"color: #A0A070;\">{}</span>".format(entry.get("value")) if entry.get("value") else ""
    }
    for entry in ENGINE_NON_FUNCTIONS
    if "type" in entry
]

MUTUALLY_EXCLUSIVE_MACROS = [
    {
        "SCRIPT_STAGE",
        "SCRIPT_PACKAGE"
    }
]

INCLUDE_REGEX = re.compile(r'#include\s+"(.+?)"')

FRIEND_REGEX = re.compile(r'\/\/\/\/\s*friend\s+"(.+?)"')

ENGINE_FUNC_REGEX = re.compile(r"^(\w+::)?([A-Za-z_]\w*)\((.*?)\)$")

TYPE_PATTERN = r"(?:bool|char|float|string|int|object|ptr|fn|tenv|var|let|real)"

FUNC_PATTERN = r"func|function|task|sub|fcall|tcall"

BLOCK_PATTERN = r"local|async|if|else|for\s+each|for|do|while|ascent|descent|loop|times|case|others"

BLOCK_ARGS_KEYWORDS = [
    "if",
    "for",
    "each",
    "in",
    "ref",
    "while",
    "ascent",
    "descent",
    "loop",
    "times",
    "alternative",
    "case",
    "bool",
    "char",
    "float",
    "string",
    "int",
    "return"
]

FUNC_KEYWORD_REGEX = re.compile(
    r"\b({func_pattern})\b".format(func_pattern=FUNC_PATTERN),
    re.VERBOSE
)

ENGINE_AT_REGEX = re.compile(
    r"({})".format("|".join(re.escape(sig) for sig in ENGINE_AT_SIGS)),
    re.VERBOSE
)

SCOPE_KEYWORD_REGEX = re.compile(
    r"\b({func_pattern}|{block_pattern})\b"
        .format(func_pattern=FUNC_PATTERN, block_pattern=BLOCK_PATTERN),
    re.VERBOSE
)

USER_DEFINED_FUNC_TASK_SUB_REGEX = re.compile(
    r"""
    (?:\/\*\*\*(?P<doc>(?:(?!\/\*\*\*).)*?)\*\*\*\/\s*)?
    (?P<kind>{func_pattern})
    (?:<(?P<rtype>[^>]+)>)?
    \s+
    (?P<name>[A-Za-z_]\w*)
    \s*
    \(
        (?P<params>[^)]*)
    \)
    """.format(func_pattern=FUNC_PATTERN),
    re.DOTALL | re.VERBOSE
)

USER_DEFINED_VARIABLE_REGEX = re.compile(
    r"""
    (?:\/\*\*\*(?P<doc>(?:(?!\/\*\*\*).)*?)\*\*\*\/\s*)?
    (?=(?:const\s+|\b{type_pattern}\b))
    (?P<const>const\s+)?
    (?:(?P<type>\b{type_pattern}\b(?:\[\])*)\s+)?
    (?P<name>[A-Za-z_]\w*)
    (?:\s*=\s*(?P<value>[^;]+))?
    \s*;
    """.format(type_pattern=TYPE_PATTERN),
    re.VERBOSE | re.DOTALL
)

ASCENT_DESCENT_REGEX = re.compile(
    r"""
    \b(?P<loop>ascent|descent)\s*
    \(\s*
        (?:(?P<type>\b{type_pattern}\b(?:\[\])*)\s+)?
        (?P<name>[A-Za-z_]\w*)
        \s+in\s+
        (?P<value>[^)]+) # everything up to ')'
    \)
    """.format(type_pattern=TYPE_PATTERN),
    re.VERBOSE | re.DOTALL
)

FOREACH_REGEX = re.compile(
    r"""
    \b(?P<loop>for\s+each)\s*
    \(\s*
    \(?
    (?:
        (?:(?P<type>\b{type_pattern}\b(?:\[\])*)\s+)?
        (?P<name>[A-Za-z_]\w*)
        (?:
            \s*,\s*
            (?:(?P<type2>\b{type_pattern}\b(?:\[\])*)\s+)?
            (?P<name2>[A-Za-z_]\w*)
        )?
    )
    \)?
    \s*
    """.format(type_pattern=TYPE_PATTERN),
    re.VERBOSE | re.DOTALL
)

IDENTIFIER_MASK_REGEX = re.compile(
    r"""
    (?<!\w)0[x][0-9A-Fa-f][0-9A-Fa-f_]* # hex literals
    |
    (?<!\w)0[o][0-7][0-7_]* # octal literals
    |
    (?<!\w)0[b][0-1][0-1_]* # binary literals
    |
    (?<!\w)\d[\d_]*\.?[\d_]*[eE][+-]?\d[\d_]*[fFiI]? # scientific notation
    |
    (?<!\w)\d[\d_]*\.[\d_]*[fFiI]? # float with decimal
    |
    (?<!\w)\d[\d_]*[fFiI]? # integer / float with suffix
    """,
    re.VERBOSE
)

IDENTIFIER_REGEX = re.compile(r"[#@]?[A-Za-z_]\w*", re.VERBOSE | re.DOTALL)

IDENTIFIER_FUNC_REGEX = re.compile(r"\b(?P<name>[A-Za-z_]\w*)\s*\(", re.VERBOSE | re.DOTALL)

NAME_COLORS = {
    "task": "#6FFFB0",
    "obj-func": "#5290DF",
    "non-task": "#40CEDF",

    "constant": "#FFBFCF",
    "user-constant": "#CF4F2F",
    "global-variable": "#D7FF74",
    "param-variable": "#FF6030"
}

_user_included_definitions_cache = {}


def clear_cache():
    
    global _user_included_definitions_cache

    _user_included_definitions_cache = {}


def remove_comments(text):

    text = re.sub(r'\/\/.*', '', text)

    text = re.sub(r'\/\*.*?\*\/', '', text, flags=re.S)

    return text


def remove_comments_preserve_length(text):

    def replacer(match):
        return " " * len(match.group(0))

    text = re.sub(r'\/\/.*', replacer, text)

    text = re.sub(r'\/\*.*?\*\/', replacer, text, flags=re.S)

    return text


def remove_comments_and_trim(text):

    text = re.sub(r'\/\*.*?\*\/', '', text, flags=re.S)

    text = re.sub(r'^[ \t]*\/\/.*(?:\r?\n|$)', '', text, flags=re.M)
    text = re.sub(r'^[ \t]*\r?\n', '', text, flags=re.M)

    return text


# def remove_strings_preserve_length(text):

#     def replacer(match):
#         return " " * len(match.group(0))

#     text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', replacer, text)

#     return text


def remove_strings_preserve_length(text):

    def replacer(match):
        s = match.group(0)
        return s[0] + " " * (len(s) - 2) + s[-1]

    text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', replacer, text)

    return text


def preceded_by_paren_or_comma(text, pos):

    i = pos - 1

    while i >= 0 and text[i].isspace():
        i -= 1

    return i >= 0 and (text[i] == '(' or text[i] == ',')


def preceded_by_any(text, pos, patterns):

    last_match = None

    regex = re.compile("|".join("(?:{})".format(p) for p in patterns))

    for m in regex.finditer(text[:pos]):
        last_match = m

    return last_match is not None and last_match.end() == pos


def uses_return_value(text, pos):

    i = pos - 1

    while i >= 0 and text[i].isspace():
        i -= 1

    if i < 0:
        return False

    operators = (
        '~', '!', '%', '^', '&', '*', '(', '-', '+', '=',
        '[', '|',
        ':',
        ',', '<', '>', '/', '?'
    )

    if text[i] in operators:
        return True

    if text[i].isalnum():

        keywords = (
            "if", "in", "ref", "return"
        )

        end = i

        while i >= 0 and (text[i].isalnum()):
            i -= 1

        word = text[(i + 1):(end + 1)]

        return word in keywords

    return False


def has_semicolon_outside_parens(text):

    depth = 0

    for ch in text:

        if ch == "(":
            depth += 1

        elif ch == ")":
            depth -= 1

        elif ch == ";" and depth == 0:
            return True

    return False


def compute_scope_ranges(text):

    stack = []
    scopes = []
    
    for i, ch in enumerate(text):
        if ch == "{":
            window_start = stack[-1][1] + 1 if stack else 0
            window = text[window_start:i]

            match = None
            for m in SCOPE_KEYWORD_REGEX.finditer(window):
                match = m

            if match and has_semicolon_outside_parens(window[match.end():]):
                match = None

            func_match = FUNC_KEYWORD_REGEX.match(match.group()) if match else None

            scope_start = (window_start + match.start()) if match else i
            function_label = func_match.group(1) if func_match else None
            stack.append((scope_start, i, function_label))

        elif ch == "}":
            if stack:
                start, _, function_label = stack.pop()
                scopes.append((start, i, function_label))
    
    return scopes


def find_scope_stack(scopes, pos):

    return [
        (start, end, function_label)
        for start, end, function_label in scopes
        if start < pos < end
    ]


def compute_ifdef_branches(text):

    branches = []
    stack = []
    
    for match in re.finditer(r"^[ \t]*(#ifdef|#ifndef|#else|#endif)(?:[ \t]+(\w+))?", text, re.MULTILINE):
        directive = match.group(1)
        macro = match.group(2)
        
        if directive == "#ifdef":
            stack.append((match.start(), {"ifdef": [macro]}))

        elif directive == "#ifndef":
            stack.append((match.start(), {"ifndef": [macro]}))

        elif directive == "#else":
            if stack:
                branch_start, active_macros = stack.pop()
                branches.append((branch_start, match.start(), active_macros))
                # invert the macros for the else branch
                inverted = {
                    "ifndef" if k == "ifdef" else "ifdef": v
                    for k, v in active_macros.items()
                }
                stack.append((match.start(), inverted))

        elif directive == "#endif":
            if stack:
                branch_start, active_macros = stack.pop()
                branches.append((branch_start, match.end(), active_macros))
    
    return branches


def find_ifdef_branch(branches, pos):

    for start, end, active_macros in branches:
        if start < pos < end:
            return active_macros

    return None


def ifdef_branches_compatible(branch_a, branch_b):

    if branch_a is None or branch_b is None:
        return branch_a == branch_b
    
    ifdefs_a = set(branch_a.get("ifdef", []))
    ifdefs_b = set(branch_b.get("ifdef", []))
    ifndefs_a = set(branch_a.get("ifndef", []))
    ifndefs_b = set(branch_b.get("ifndef", []))
    
    # incompatible if one requires a macro the other forbids
    if ifdefs_a & ifndefs_b or ifdefs_b & ifndefs_a:
        return False
    
    # incompatible if both require mutually exclusive macros
    for exclusive_group in MUTUALLY_EXCLUSIVE_MACROS:
        if ifdefs_a & exclusive_group and ifdefs_b & exclusive_group and not ifdefs_a & ifdefs_b:
            return False
    
    return True


def resolve_include(base_file, relative_path):

    if not os.path.isabs(relative_path):
        relative_path = relative_path.strip()

    base_dir = os.path.dirname(base_file)
    full_path = os.path.normpath(os.path.join(base_dir, relative_path))

    return full_path


def get_dnh_files(file_path):

    if not file_path.lower().endswith(".dnh"):
        return []

    current_dir = os.path.abspath(
        file_path if os.path.isdir(file_path) else os.path.dirname(file_path)
    )

    root_dir = None
    search_dir = current_dir

    while True:

        if any(f.lower().endswith(".exe") for f in os.listdir(search_dir)):
            root_dir = search_dir
            break

        parent_dir = os.path.dirname(search_dir)

        if search_dir == parent_dir:
            break

        search_dir = parent_dir

    if root_dir is None:
        print("No directory containing a .exe file was found.")
        return []

    dnh_files = []

    for root, _, files in os.walk(root_dir):

        for name in files:

            if name.lower().endswith(".dnh"):
                dnh_files.append(os.path.abspath(os.path.join(root, name)))

    return dnh_files


def parse_definitions_from_content(content, pos=0, full_search=False, source_file=None, entry_scope="", external=False, friend=False):

    function_entries = []
    variable_entries = []
    at_entries = []

    filtered_content = remove_strings_preserve_length(remove_comments_preserve_length(content))

    scopes = compute_scope_ranges(filtered_content)
    scope_stack = find_scope_stack(scopes, pos)

    ifdef_branches = compute_ifdef_branches(filtered_content)

    for match in USER_DEFINED_FUNC_TASK_SUB_REGEX.finditer(content):

        if content[match.start("name")] != filtered_content[match.start("name")]:
            continue

        function_scope_stack = find_scope_stack(scopes, match.start())
        minimal_scope = function_scope_stack[0] if (function_scope_stack and len(function_scope_stack) > 0) else None

        if not full_search:

            if minimal_scope is not None and minimal_scope not in scope_stack:
                continue

        function_ifdef_branch = find_ifdef_branch(ifdef_branches, match.start())

        name = match.group("name")
        kind = match.group("kind")
        rtype = match.group("rtype")

        if not rtype:
            rtype = "void" if kind in ("sub", "fcall", "tcall") else ("tenv" if kind == "task" else "unspecified")

        raw_doc = match.group("doc") or "No documentation."
        doc = raw_doc.strip()

        params_raw = match.group("params").strip()

        param_names = []
        param_types = []

        if params_raw:
            parts = [p.strip() for p in params_raw.split(",")]

            for p in parts:
                tokens = p.split()

                if len(tokens) >= 2:
                    param_types.append(tokens[0])
                    param_names.append(tokens[1])

                elif len(tokens) == 1:
                    param_types.append("any")
                    param_names.append(tokens[0])

        line_number = content.count("\n", 0, match.start("name")) + 1 # + raw_doc.count("\n") + (1 if match.group("doc") else 0)

        line_begin_pos = content.rfind("\n", 0, match.start("name")) + 1
        name_start = match.start("name") - line_begin_pos
        name_end = name_start + len(name)

        function_entry = {
            "scope": entry_scope,
            "trigger": name,
            "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
            "kind": kind,
            "params": param_names,
            "param_types": param_types,
            "return_type": rtype,
            "doc": doc,
            "language": "User Defined",
            "source_file": source_file,
            "line_number": line_number,
            "line_position": (name_start, name_end),
            "scope_stack": function_scope_stack,
            "minimal_scope": minimal_scope,
            "ifdef": function_ifdef_branch,
            "is_function": True,
            "is_isolated": True if kind in ("fcall", "tcall") else False
        }

        if external:
            function_entry["external"] = True

        if friend:
            function_entry["friend"] = True

        function_entries.append(function_entry)

        brace_pos = filtered_content.find("{", match.end())
        parameter_scope_stack = find_scope_stack(scopes, brace_pos + 1)
        minimal_parameter_scope = parameter_scope_stack[0] if (parameter_scope_stack and len(parameter_scope_stack) > 0) else None

        if minimal_parameter_scope is not None and (full_search or ((minimal_parameter_scope in scope_stack and pos <= minimal_parameter_scope[1]) or match.start("params") <= pos <= match.end("params"))):
            name_type = "non-task"

            if len(name) > 0 and name[0] == "_":
                name_type = "task"
            elif len(name) > 2 and name[0:3] == "Obj":
                name_type = "obj-func"

            param_search = content[match.end("name"):match.end("params")]
            param_parts = [p.strip() for p in param_search.split(",")]

            for i, (param_name, param_type) in enumerate(zip(param_names, param_types)):

                part_start = param_search.find(param_parts[i])
                part_name_offset = param_parts[i].rfind(param_name)

                parameter_found = match.end("name") + part_start + part_name_offset
                # parameter_found = match.end("name") + content[match.end("name"):match.end("params")].find(param_name)
                parameter_line_number = line_number + content.count("\n", match.start("name"), parameter_found)

                parameter_line_begin_pos = content.rfind("\n", 0, parameter_found) + 1
                parameter_name_start = parameter_found - parameter_line_begin_pos
                parameter_name_end = parameter_name_start + len(param_name)

                variable_entry = {
                    "scope": entry_scope,
                    "trigger": param_name,
                    "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
                    "type": param_type,
                    "value": "<span style=\"color: hsl(261, 100%, 75%);\">Parameter {}</span> of <span style=\"color: {};\">{}</span>".format(i + 1, NAME_COLORS.get(name_type, "#40CEDF"), name),
                    "doc": "",
                    "language": "User Defined",
                    "source_file": source_file,
                    "line_number": parameter_line_number,
                    "line_position": (parameter_name_start, parameter_name_end),
                    "scope_stack": parameter_scope_stack,
                    "minimal_scope": minimal_parameter_scope,
                    "ifdef": function_ifdef_branch,
                    "is_parameter": True
                }

                if external:
                    variable_entry["external"] = True

                if friend:
                    variable_entry["friend"] = True

                variable_entries.append(variable_entry)

    # seen_parameters = [entry["trigger"] for entry in variable_entries]

    for match in itertools.chain(
        USER_DEFINED_VARIABLE_REGEX.finditer(content),
        ASCENT_DESCENT_REGEX.finditer(content),
        FOREACH_REGEX.finditer(content)
    ):

        name_count = 1

        while "name" + str(name_count + 1) in match.groupdict():
            name_count += 1

        for i in range(0, name_count):
            dict_suffix = "" if i == 0 else str(i + 1)

            dict_name = "name" + dict_suffix
            dict_type = "type" + dict_suffix

            if not match.group(dict_name):
                continue

            if content[match.start(dict_name)] != filtered_content[match.start(dict_name)]:
                continue

            name = match.group(dict_name)

            # if name in seen_parameters:
            #     continue

            if ("loop" in match.groupdict()) or preceded_by_paren_or_comma(content, match.start()):
                brace_pos = filtered_content.find("{", match.end())
                var_scope_stack = find_scope_stack(scopes, brace_pos + 1)
                minimal_scope = var_scope_stack[0] if (var_scope_stack and len(var_scope_stack) > 0) else None

            else:
                var_scope_stack = find_scope_stack(scopes, match.start())
                minimal_scope = var_scope_stack[0] if (var_scope_stack and len(var_scope_stack) > 0) else None

            if not full_search:

                if minimal_scope is not None and minimal_scope not in scope_stack:
                    continue

                if minimal_scope is not None and pos > minimal_scope[1]:
                    continue

            # omit variable definitions in viewed file past cursor (variables only, not functions)

            if len(entry_scope) > 0 and match.start() > pos:
                continue

            has_const = "const" in match.groupdict() and match.group("const")

            type = "const {}".format(match.group(dict_type)) if has_const else match.group(dict_type)

            if type is None:
                type = "const var" if has_const else "var"

            elif has_const and match.group(dict_type) is None:
                type = "const var"

            has_doc = "doc" in match.groupdict() and match.group("doc")

            raw_doc = match.group("doc") if has_doc else "No documentation."
            doc = raw_doc.strip()

            has_value = "value" in match.groupdict() and match.group("value")

            value = remove_comments_and_trim(match.group("value").strip()).replace("\n", "<br>").replace("\t", "&emsp;&emsp;") if has_value else ""

            var_ifdef_branch = find_ifdef_branch(ifdef_branches, match.start())

            line_number = content.count("\n", 0, match.start(dict_name)) + 1 # + raw_doc.count("\n") + (1 if has_doc else 0)

            line_begin_pos = content.rfind("\n", 0, match.start(dict_name)) + 1
            name_start = match.start(dict_name) - line_begin_pos
            name_end = name_start + len(name)

            variable_entry = {
                "scope": entry_scope,
                "trigger": name,
                "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
                "type": type,
                "value": "<span style=\"color: #A0A070;\">{}</span>".format(value) if has_value else None,
                "doc": doc,
                "language": "User Defined",
                "source_file": source_file,
                "line_number": line_number,
                "line_position": (name_start, name_end),
                "scope_stack": var_scope_stack,
                "minimal_scope": minimal_scope,
                "ifdef": var_ifdef_branch
            }

            if external:
                variable_entry["external"] = True

            if friend:
                variable_entry["friend"] = True

            variable_entries.append(variable_entry)

    for match in ENGINE_AT_REGEX.finditer(filtered_content):
        at_scope_stack = find_scope_stack(scopes, match.start())
        minimal_scope = at_scope_stack[0] if (at_scope_stack and len(at_scope_stack) > 0) else None

        line_number = content.count("\n", 0, match.start()) # + 1

        line_begin_pos = content.rfind("\n", 0, match.start()) + 1
        name_start = match.start() - line_begin_pos
        name_end = name_start + len(match.group())

        at_ifdef_branch = find_ifdef_branch(ifdef_branches, match.start())

        at_entry = {
            "scope": entry_scope,
            "name": match.group(),
            "source_file": source_file,
            "line_number": line_number,
            "line_position": (name_start, name_end),
            "scope_stack": at_scope_stack,
            "minimal_scope": minimal_scope,
            "ifdef": at_ifdef_branch
        }

        if external:
            at_entry["external"] = True

        if friend:
            at_entry["friend"] = True

        at_entries.append(at_entry)

    return function_entries, variable_entries, at_entries, scopes, scope_stack


def extract_user_definitions_everywhere(file_path):

    functions = []
    variables = []
    ats = []

    dnh_files = get_dnh_files(file_path)

    for dnh_file in dnh_files:

        if file_path == dnh_file:
            continue

        try:
            with open(dnh_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        internal_functions, internal_variables, internal_ats, _, _ = parse_definitions_from_content(
            content,
            pos=0,
            full_search=False,
            source_file=dnh_file,
            external=True
        )

        functions.extend(internal_functions)
        variables.extend(internal_variables)
        ats.extend(internal_ats)

    return functions, variables, ats


def extract_user_definitions(view_file_name, view_content, view_scope_name="", location=None, full_search=False):

    global _user_included_definitions_cache

    if not view_file_name:
        return [], []

    view_file_name = os.path.abspath(view_file_name)

    if not view_file_name.lower().endswith(".dnh"):
        return [], []

    visited = set()

    functions = []
    variables = []
    ats = []

    def extract_user_definitions_recurse(file_path, offset=None, inclusion_root=None, caching=False, friend=False):

        if file_path in visited:
            return

        visited.add(file_path)

        if not os.path.exists(file_path):
            return

        is_view_file = False

        if os.path.abspath(view_file_name) == file_path:
            content = view_content
            is_view_file = True

        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                return

        internal_functions, internal_variables, internal_ats, scopes, scope_stack = parse_definitions_from_content(
            content,
            pos=offset if offset else 0,
            full_search=full_search,
            source_file=file_path,
            entry_scope=view_scope_name if os.path.abspath(view_file_name) == file_path else "",
            friend=friend
        )

        functions.extend(internal_functions)
        variables.extend(internal_variables)
        ats.extend(internal_ats)

        if caching:
            if inclusion_root in _user_included_definitions_cache:
                _user_included_definitions_cache[inclusion_root][0].extend(internal_functions)
                _user_included_definitions_cache[inclusion_root][1].extend(internal_variables)
                _user_included_definitions_cache[inclusion_root][2].extend(internal_ats)
            else:
                _user_included_definitions_cache[inclusion_root] = (internal_functions, internal_variables, internal_ats)

        for match in INCLUDE_REGEX.finditer(remove_comments(content)):

            # TODO: the position and scope cutoffs don't seem to work properly

            if offset and match.start() > offset:
                continue

            include_scope_stack = find_scope_stack(scopes, match.start())
            minimal_scope = include_scope_stack[0] if (include_scope_stack and len(include_scope_stack) > 0) else None

            if minimal_scope is not None and minimal_scope not in scope_stack:
                continue

            relative_path = match.group(1)
            included_file = resolve_include(file_path, relative_path)

            cache_key = view_file_name + "_" + included_file

            if cache_key in _user_included_definitions_cache:
                downward_functions, downward_variables, downward_ats = _user_included_definitions_cache[cache_key]

                functions.extend(downward_functions)
                variables.extend(downward_variables)
                ats.extend(downward_ats)

            else:
                extract_user_definitions_recurse(included_file, inclusion_root=(cache_key if is_view_file else inclusion_root), caching=True, friend=friend)

        if not is_view_file:
            return

        for match in FRIEND_REGEX.finditer(content):

            if offset and match.start() > offset:
                continue

            friend_scope_stack = find_scope_stack(scopes, match.start())
            minimal_scope = friend_scope_stack[0] if (friend_scope_stack and len(friend_scope_stack) > 0) else None

            if minimal_scope is not None and minimal_scope not in scope_stack:
                continue

            relative_path = match.group(1)
            included_file = resolve_include(file_path, relative_path)

            cache_key = view_file_name + "_" + included_file

            if cache_key in _user_included_definitions_cache:
                downward_functions, downward_variables, downward_ats = _user_included_definitions_cache[cache_key]

                functions.extend(downward_functions)
                variables.extend(downward_variables)
                ats.extend(downward_ats)

            else:
                extract_user_definitions_recurse(included_file, inclusion_root=included_file, caching=True, friend=True)

    extract_user_definitions_recurse(view_file_name, offset=location)

    return functions, variables, ats


def get_call_argument_info(content):
    size = len(content)

    if size == 0:
        return None

    if content[0] != '(':
        return None

    depth = 0
    comma_count = 0
    i = 0

    for ch in content:

        if ch == '(' or ch == '[':
            depth += 1

        elif ch == ')' or ch == ']':
            depth -= 1
            if depth <= 0:
                break

        elif ch == ',' and depth == 1:
            comma_count += 1

        if ch != ' ':
            i += 1

    if i == 1:
        return 0

    return comma_count + 1
