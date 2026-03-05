import sublime
import sublime_plugin
import re
import html
import textwrap
import os
from difflib import SequenceMatcher


ENGINE_NON_FUNCTIONS = [
    { "sig": "doc", "lang": "vibrant-sx", "kind": sublime.KIND_SNIPPET, "completion": "/***\n$0\n***/" },
    { "sig": "ext", "lang": "vibrant-sx", "kind": sublime.KIND_SNIPPET, "completion": "//// external dependency" },
    { "sig": "friend", "lang": "vibrant-sx", "kind": sublime.KIND_SNIPPET, "completion": "//// friend \"./path.dnh\"" },

    { "sig": "local", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "local\n{\n\t$0\n}" },
    { "sig": "function", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "function Fun()\n{\n\t$0\n}" },
    { "sig": "function", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "function<void> Fun()\n{\n\t$0\n}", "desc": "function<return-type>" },
    { "sig": "func", "lang": "ph3sx-zlabel", "kind": sublime.KIND_KEYWORD, "completion": "func Fun()\n{\n\t$0\n}" },
    { "sig": "func", "lang": "ph3sx-zlabel", "kind": sublime.KIND_KEYWORD, "completion": "func<void> Fun()\n{\n\t$0\n}", "desc": "func<return-type>" },
    { "sig": "sub", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "sub Sub()\n{\n\t$0\n}" },
    { "sig": "task", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "task _Task()\n{\n\t$0\n}" },
    { "sig": "async", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "async\n{\n\t$0\n}" },

    { "sig": "case", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "case (value)\n{\n\t$0\n}" },
    { "sig": "others", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "others\n{\n\t$0\n}" },
    { "sig": "do", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "do\n{\n\t$0\n}" },
    { "sig": "else", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "else\n{\n\t$0\n}" },
    { "sig": "for", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "for (int i = 0; i < n; i++)\n{\n\t$0\n}", "desc": "Standard for-loop: for (int i = 0, i < n; i++)" },
    { "sig": "for", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "for each (var item in ref arr)\n{\n\t$0\n}", "desc": "Standard for-each-loop: for each (var item in ref arr)" },
    { "sig": "for", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "for each ((int index, var item) in ref arr)\n{\n\t$0\n}", "desc": "Enumerating for-each-loop: for each ((int index, var item) in ref arr)" },
    { "sig": "each", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "each (var item in ref arr)\n{\n\t$0\n}", "desc": "Standard for-each-loop: for each (var item in ref arr)" },
    { "sig": "each", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "each ((int index, var item) in ref arr)\n{\n\t$0\n}", "desc": "Enumerating for-each-loop: for each ((int index, var item) in ref arr)" },
    { "sig": "in", "lang": "ph3", "kind": sublime.KIND_KEYWORD },
    { "sig": "ref", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD },
    { "sig": "ascent", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "ascent (i in 0..n)\n{\n\t$0\n}" },
    { "sig": "ascent", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "ascent (int i in 0..n)\n{\n\t$0\n}" },
    { "sig": "descent", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "descent (i in 0..n)\n{\n\t$0\n}" },
    { "sig": "descent", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "descent (int i in 0..n)\n{\n\t$0\n}" },
    { "sig": "loop", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "loop\n{\n\t$0\n}", "desc": "loop (Infinite loop)" },
    { "sig": "loop", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "loop (n)\n{\n\t$0\n}", "desc": "loop (n) (Finite loop)" },
    { "sig": "if", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "if (cond)\n{\n\t$0\n}" },
    { "sig": "alternative", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "alternative (state)\n\ncase (value)\n{\n\t$0\n}\n\nothers\n{\n\t\n}" },
    { "sig": "while", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "while (cond)\n{\n\t$0\n}" },
    { "sig": "times", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "times (n)\n{\n\t$0\n}" },

    { "sig": "return", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "return;" },
    { "sig": "continue", "lang": "ph3sx", "kind": sublime.KIND_KEYWORD, "completion": "continue;" },
    { "sig": "break", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "break;" },

    { "sig": "yield", "lang": "ph3", "kind": sublime.KIND_KEYWORD, "completion": "yield;" },

    { "sig": "bool", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "char", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "float", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "string", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "int", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "var", "lang": "ph3", "kind": sublime.KIND_TYPE },
    { "sig": "let", "lang": "ph3", "kind": sublime.KIND_TYPE },
    { "sig": "real", "lang": "ph3 EXCLUSIVE", "kind": sublime.KIND_TYPE, "desc": "Only available in ph3. Removed as of ph3sx." },
    { "sig": "const", "lang": "ph3sx", "kind": sublime.KIND_TYPE },
    { "sig": "void", "lang": "ph3sx", "kind": sublime.KIND_TYPE },

    { "sig": "@Loading", "lang": "ph3", "kind": sublime.KIND_NAMESPACE, "completion": "@Loading\n{\n\t$0\n}" },
    { "sig": "@Initialize", "lang": "ph3", "kind": sublime.KIND_NAMESPACE, "completion": "@Initialize\n{\n\t$0\n}" },
    { "sig": "@Event", "lang": "ph3", "kind": sublime.KIND_NAMESPACE, "completion": "@Event\n{\n\talternative (GetEventType())\n\n\tcase (EV_USER)\n\t{\n\t\t$0\n\t}\n}" },
    { "sig": "@MainLoop", "lang": "ph3", "kind": sublime.KIND_NAMESPACE, "completion": "@MainLoop\n{\n\t$0\n\n\tyield;\n}" },
    { "sig": "@Finalize", "lang": "ph3", "kind": sublime.KIND_NAMESPACE, "completion": "@Finalize\n{\n\t$0\n}" },

    { "sig": "#ScriptVersion", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#ScriptVersion[3]" },
    { "sig": "#TouhouDanmakufu", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#TouhouDanmakufu[Single/Plural/Stage/Player/Package]" },
    { "sig": "#Title", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#Title[\"text\"]" },
    { "sig": "#Text", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#Text[\"text\"]" },
    { "sig": "#Image", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#Image[\"./path.ext\"]" },
    { "sig": "#Player", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#Player[\"./path1.dnh\", \"./path2.dnh\"...]" },
    { "sig": "#ID", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#ID[\"text\"]" },
    { "sig": "#ReplayName", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#ReplayName[\"text\"]" },
    { "sig": "#System", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#System[\"./path.dnh\"]" },
    { "sig": "#Title", "lang": "ph3", "kind": sublime.KIND_MARKUP, "completion": "#Title[\"Name\"]" },

    { "sig": "#include", "lang": "ph3", "kind": sublime.KIND_NAVIGATION, "completion": "#include \"./path.dnh\"" },

    { "sig": "#if", "lang": "ph3sx", "kind": sublime.KIND_MARKUP, "completion": "#if cond\n\n\t$0\n\n#elif cond\n\n\t\n\n#else\n\n\t\n\n#endif" },
    { "sig": "#ifdef", "lang": "ph3sx", "kind": sublime.KIND_MARKUP, "completion": "#ifdef macro /* one of _DNH_PH3SX_ / _DNH_PH3SX_ZLABEL_ / SCRIPT_STAGE / SCRIPT_PACKAGE */\n\n\t$0\n\n#else\n\n\t\n\n#endif" },
    { "sig": "#ifndef", "lang": "ph3sx", "kind": sublime.KIND_MARKUP, "completion": "#ifndef macro /* one of _DNH_PH3SX_ / _DNH_PH3SX_ZLABEL_ / SCRIPT_STAGE / SCRIPT_PACKAGE */\n\n\t$0\n\n#else\n\n\t\n\n#endif" },
    { "sig": "#elif", "lang": "ph3sx", "kind": sublime.KIND_MARKUP, "completion": "#elif cond\n\n\t" },
    { "sig": "#elif", "lang": "ph3sx", "kind": sublime.KIND_MARKUP, "completion": "#else\n\n\t" },
    { "sig": "#endif", "lang": "ph3sx", "kind": sublime.KIND_MARKUP },

    { "sig": "#UserShotData", "lang": "ph3", "kind": sublime.KIND_MARKUP },
    { "sig": "#UserItemData", "lang": "ph3", "kind": sublime.KIND_MARKUP },

    # Constants

    { "sig": "_DNH_PH3SX_", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "_DNH_PH3SX_ZLABEL_", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SCRIPT_STAGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SCRIPT_PACKAGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "KEY_INVALID", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "-1" },
    { "sig": "VK_LEFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_RIGHT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_UP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_SHOT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_BOMB", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_SLOWMOVE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_USER1", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_USER2", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_OK", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_CANCEL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_PAUSE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_USER_ID_STAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VK_USER_ID_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "STATUS_INVALID", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATUS_LOADED", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATUS_LOADING", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATUS_RUNNING", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATUS_PAUSED", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATUS_CLOSING", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "STAGE_STATE_FINISHED", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "STAGE_RESULT_BREAK_OFF", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STAGE_RESULT_PLAYER_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STAGE_RESULT_CLEARED", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "NULL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "0" },

    { "sig": "INF", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "infinity float" },
    { "sig": "NAN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "NaN float" },

    { "sig": "FLOAT_TYPE_SUBNORMAL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FLOAT_TYPE_NORMAL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FLOAT_TYPE_ZERO", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FLOAT_TYPE_INFINITY", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FLOAT_TYPE_NAN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "VAR_INT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VAR_FLOAT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VAR_CHAR", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VAR_BOOL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VAR_ARRAY", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "VAR_STRING", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "LERP_LINEAR", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LERP_SMOOTH", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LERP_SMOOTHER", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LERP_ACCELERATE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LERP_DECELERATE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "M_PI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "3.14159265358979323846" },
    { "sig": "M_PI_2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.57079632679489661923" },
    { "sig": "M_PI_4", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.78539816339744830962" },
    { "sig": "M_PI_X2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "6.28318530717958647693" },
    { "sig": "M_PI_X4", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "12.5663706143591729539" },
    { "sig": "M_1_PI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.31830988618379067154" },
    { "sig": "M_2_PI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.63661977236758134308" },
    { "sig": "M_SQRTPI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.772453850905516027298" },
    { "sig": "M_1_SQRTPI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.56418958354775628695" },
    { "sig": "M_2_SQRTPI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.128379167095512573896" },
    { "sig": "M_SQRT2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.4142135623730950488" },
    { "sig": "M_SQRT2_2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.7071067811865475244" },
    { "sig": "M_SQRT2_X2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "2.8284271247461900976" },
    { "sig": "M_E", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "2.71828182845904523536" },
    { "sig": "M_LOG2E", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.44269504088896340736" },
    { "sig": "M_LOG10E", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.43429448190325182765" },
    { "sig": "M_LN2", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.69314718055994530942" },
    { "sig": "M_LN10", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "2.30258509299404568402" },
    { "sig": "M_PHI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "1.61803398874989484821" },
    { "sig": "M_1_PHI", "lang": "ph3sx", "type": "const float", "kind": sublime.KIND_VARIABLE, "value": "0.6180339887498948482" },

    { "sig": "ID_INVALID", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "-1" },
    { "sig": "OBJ_BASE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_PRIMITIVE_2D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPRITE_2D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPRITE_LIST_2D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_PRIMITIVE_3D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPRITE_3D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_TRAJECTORY_3D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_PARTICLE_LIST_2D", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_PARTICLE_LIST_3D", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SHADER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_MESH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_TEXT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SOUND", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_FILE_TEXT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_FILE_BINARY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "COLOR_PERMUTE_ARGB", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_RGBA", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_BGRA", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_RGB", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_BGR", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_A", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_R", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_G", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "COLOR_PERMUTE_B", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "BLEND_NONE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_ALPHA", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_ADD_RGB", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_ADD_ARGB", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_MULTIPLY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_SUBTRACT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_SHADOW", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_INV_DESTRGB", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BLEND_ALPHA_INV", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "CULL_NONE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CULL_CW", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CULL_CCW", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "IFF_BMP", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "IFF_JPG", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "IFF_TGA", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "IFF_PNG", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "IFF_DDS", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "IFF_PPM", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "FILTER_NONE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FILTER_POINT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FILTER_LINEAR", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "FILTER_ANISOTROPIC", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "CAMERA_NORMAL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CAMERA_LOOKAT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "PRIMITIVE_POINT_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PRIMITIVE_LINELIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PRIMITIVE_LINESTRIP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PRIMITIVE_TRIANGLELIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PRIMITIVE_TRIANGLESTRIP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PRIMITIVE_TRIANGLEFAN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "BORDER_NONE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BORDER_FULL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "BORDER_SHADOW", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ALIGNMENT_LEFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ALIGNMENT_RIGHT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ALIGNMENT_CENTER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ALIGNMENT_TOP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ALIGNMENT_BOTTOM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "CHARSET_ANSI", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_DEFAULT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_SHIFTJIS", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_HANGUL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_JOHAB", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_CHINESEBIG5", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_TURKISH", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_VIETNAMESE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_HEBREW", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_ARABIC", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CHARSET_THAI", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "SOUND_BGM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SOUND_SE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SOUND_VOICE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "SOUND_UNKNOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SOUND_WAVE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "SOUND_OGG", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_FORMAT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_CHANNEL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SAMPLE_RATE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_AVG_BYTE_PER_SEC", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_BLOCK_ALIGN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_BIT_PER_SAMPLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_POSITION", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_POSITION_SAMPLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_LENGTH", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_LENGTH_SAMPLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "CODE_ACP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CODE_UTF8", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CODE_UTF16LE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "CODE_UTF16BE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ENDIAN_LITTLE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ENDIAN_BIG", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "KEY_FREE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_PUSH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_PULL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_HOLD", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "MOUSE_LEFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOUSE_RIGHT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOUSE_MIDDLE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "KEY_ESCAPE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_1", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_2", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_3", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_4", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_5", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_6", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_7", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_8", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_9", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_0", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_MINUS", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_EQUALS", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_BACK", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_TAB", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_Q", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_W", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_E", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_R", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_T", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_Y", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_U", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_I", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_O", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_P", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LBRACKET", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RBRACKET", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RETURN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LCONTROL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_A", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_S", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_D", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_G", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_H", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_J", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_K", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_L", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SEMICOLON", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_APOSTROPHE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_GRAVE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LSHIFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_BACKSLASH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_Z", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_X", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_C", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_V", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_B", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_N", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_M", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_COMMA", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_PERIOD", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SLASH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RSHIFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_MULTIPLY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LMENU", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SPACE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_CAPITAL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F1", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F2", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F3", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F4", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F5", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F6", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F7", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F8", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F9", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F10", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMLOCK", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SCROLL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD7", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD8", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD9", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SUBTRACT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD4", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD5", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD6", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_ADD", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD1", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD2", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD3", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPAD0", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_DECIMAL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F11", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F12", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F13", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F14", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_F15", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_KANA", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_CONVERT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NOCONVERT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_YEN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPADEQUALS", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_CIRCUMFLEX", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_AT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_COLON", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_UNDERLINE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_KANJI", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_STOP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_AX", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_UNLABELED", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPADENTER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RCONTROL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NUMPADCOMMA", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_DIVIDE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SYSRQ", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RMENU", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_PAUSE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_HOME", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_UP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_PRIOR", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LEFT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RIGHT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_END", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_NEXT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_INSERT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_DELETE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_LWIN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_RWIN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_APPS", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_POWER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "KEY_SLEEP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_USER_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "100000" },
    { "sig": "EV_USER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "1000000" },
    { "sig": "EV_USER_SYSTEM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "2000000" },
    { "sig": "EV_USER_STAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "3000000" },
    { "sig": "EV_USER_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "4000000" },
    { "sig": "EV_USER_PACKAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "value": "5000000" },

    { "sig": "EV_APP_LOSE_FOCUS", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_APP_RESTORE_FOCUS", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "TYPE_SCRIPT_ALL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SCRIPT_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SCRIPT_SINGLE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SCRIPT_PLURAL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SCRIPT_STAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SCRIPT_PACKAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_SCRIPT_TYPE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_PATH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_ID", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_TITLE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_TEXT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_IMAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SCRIPT_REPLAY_NAME", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "REPLAY_FILE_PATH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_DATE_TIME", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_USER_NAME", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_TOTAL_SCORE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_FPS_AVERAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_PLAYER_NAME", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_STAGE_INDEX_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_STAGE_START_SCORE_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_STAGE_LAST_SCORE_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_COMMENT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "REPLAY_INDEX_ACTIVE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_INDEX_DIGIT_MIN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_INDEX_DIGIT_MAX", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "REPLAY_INDEX_USER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "RESULT_CANCEL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "RESULT_END", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "RESULT_RETRY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "RESULT_SAVE_REPLAY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "TYPE_ALL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_SHOT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_CHILD", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_IMMEDIATE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_FADE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TYPE_ITEM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "OWNER_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OWNER_ENEMY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "DELAY_DEFAULT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "DELAY_LERP", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "PATTERN_FAN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_FAN_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_RING", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_RING_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ARROW", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ARROW_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_POLYGON", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_POLYGON_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ELLIPSE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ELLIPSE_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_SCATTER_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_SCATTER_SPEED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_SCATTER", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_LINE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_LINE_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ROSE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_ROSE_AIMED", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "PATTERN_BASEPOINT_RESET", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "TRANSFORM_WAIT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADD_SPEED_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ANGULAR_MOVE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_N_DECEL_CHANGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_GRAPHIC_CHANGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_BLEND_CHANGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_TO_SPEED_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_A1", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_A2", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_B1", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_B2", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_C1", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TRANSFORM_ADDPATTERN_C2", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "STATE_NORMAL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATE_HIT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATE_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "STATE_END", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ITEM_1UP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_1UP_S", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_SPELL_S", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_POWER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_POWER_S", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_POINT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_POINT_S", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_USER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ITEM_AUTOCOLLECT_PLAYER_SCOPE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_AUTOCOLLECT_COLLECT_ALL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_AUTOCOLLECT_POC_LINE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_AUTOCOLLECT_COLLECT_CIRCLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_AUTOCOLLECT_ALL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ITEM_MOVE_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_MOVE_TOPLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ITEM_MOVE_SCORE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "OBJ_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPELL_MANAGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_ENEMY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_ENEMY_BOSS", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_ENEMY_BOSS_SCENE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SHOT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_LOOSE_LASER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_STRAIGHT_LASER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_CURVE_LASER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SHOT_PATTERN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_ITEM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_LIFE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_DAMAGE_RATE_SHOT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_DAMAGE_RATE_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SHOT_HIT_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_DAMAGE_PREVIOUS_FRAME", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_TIMER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_TIMERF", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ORGTIMERF", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_LAST_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_DURABLE_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_REQUIRE_ALL_DOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_SPELL_SCORE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_REMAIN_STEP_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ACTIVE_STEP_LIFE_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ACTIVE_STEP_TOTAL_MAX_LIFE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ACTIVE_STEP_TOTAL_LIFE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ACTIVE_STEP_LIFE_RATE_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_LAST_STEP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_PLAYER_SHOOTDOWN_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_PLAYER_SPELL_COUNT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_CURRENT_LIFE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_CURRENT_LIFE_MAX", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_ITEM_SCORE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ITEM_MOVE_TYPE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_ITEM_TYPE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "INFO_EXISTS", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_PATH", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_RECT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_DELAY_COLOR", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_BLEND", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_COLLISION", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_COLLISION_LIST", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "INFO_IS_FIXED_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_REQUEST_LIFE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_TIMER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_IS_SPELL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_IS_LAST_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_IS_DURABLE_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_REQUIRE_ALL_DOWN", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_SPELL_SCORE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_REQUEST_REPLAY_TARGET_COMMON_AREA", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_GET_ITEM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_COLLECT_ITEM", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_CANCEL_ITEM", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_DELETE_SHOT_IMMEDIATE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_DELETE_SHOT_TO_ITEM", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_DELETE_SHOT_FADE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_GRAZE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE, "desc": "In ph3sx, this is called in a separate thread. Using rand() here WILL cause replay desyncs." },
    { "sig": "EV_HIT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_DELETE_SHOT_PLAYER", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_TIMEOUT", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_START_BOSS_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_END_BOSS_SPELL", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_GAIN_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_START_BOSS_STEP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_END_BOSS_STEP", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_PLAYER_SHOOTDOWN", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_PLAYER_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_PLAYER_REBIRTH", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "REBIRTH_DEFAULT", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_PAUSE_ENTER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "EV_PAUSE_LEAVE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "EV_REQUEST_SPELL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "TARGET_ALL", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TARGET_ENEMY", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "TARGET_PLAYER", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "MOVE_OTHER", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOVE_NONE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOVE_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOVE_XY", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOVE_XY_ANGLE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "MOVE_LINE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "TOPLAYER_CHANGE", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "NO_CHANGE", "lang": "ph3", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "UNCAPPED_MAX", "lang": "ph3sx", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "OBJ_SPLINE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "OBJ_SPRING_MASS_SYSTEM", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ANGLE_FIXED", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ANGLE_ROTATE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ANGLE_CENTER", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ANGLE_FOLLOW", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ANGLE_ABSOLUTE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ANGLE_RELATIVE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "ORDER_ANGLE_SCALE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "ORDER_SCALE_ANGLE", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },

    { "sig": "LOOP_FORWARD", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LOOP_BACKWARD", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LOOP_FORWARD_BACKWARD", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
    { "sig": "LOOP_BACKWARD_FORWARD", "lang": "ph3sx-zlabel", "type": "const int", "kind": sublime.KIND_VARIABLE },
]

ENGINE_SIGS = [non_func["sig"] for non_func in ENGINE_NON_FUNCTIONS]

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

INCLUDE_REGEX = re.compile(r'#include\s+"(.+?)"')

FRIEND_REGEX = re.compile(r'\/\/\/\/\s*friend\s+"(.+?)"')

ENGINE_FUNC_REGEX = re.compile(r"^(\w+::)?([A-Za-z_]\w*)\((.*?)\)$")

USER_DEFINED_FUNC_TASK_SUB_REGEX = re.compile(
    r"""
    (?:\/\*\*\*(?P<doc>.*?)\*\*\*\/\s*)?
    (?P<kind>func|function|task|sub)
    (?:<(?P<rtype>[^>]+)>)?
    \s+
    (?P<name>[A-Za-z_]\w*)
    \s*
    \(
        (?P<params>[^)]*)
    \)
    """,
    re.DOTALL | re.VERBOSE
)

USER_DEFINED_VARIABLE_REGEX = re.compile(
    r"""
    (?:\/\*\*\*(?P<doc>.*?)\*\*\*\/\s*)?
    (?:
        const\s+
        (?:(?P<type1>\b(?:bool|char|float|string|int|var|let|real)\b(?:\[\])*)\s+)?
        (?P<name1>[A-Za-z_]\w*)
      |
        (?P<type2>\b(?:bool|char|float|string|int|var|let|real)\b(?:\[\])*)\s+
        (?P<name2>[A-Za-z_]\w*)
    )
    (?:
        \s*=\s*
        (?P<value>\[[^\]]*\]|[^;]+)
    )?
    \s*# no semicolon
    """,
    re.VERBOSE | re.DOTALL
)

NAME_COLORS = {
    "task": "#6FFFB0",
    "obj-func": "#5290DF",
    "non-task": "#40CEDF",

    "constant": "#FFBFCF",
    "user-constant": "#CF4F2F",
    "global-variable": "#D7FF74",
    "param-variable": "#FF6030"
}

HIGHLIGHT_KEY = "hover_highlight"

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


def remove_strings_preserve_length(text):

    def replacer(match):
        return " " * len(match.group(0))

    text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', replacer, text)

    return text


def preceded_by_paren_or_comma(text, pos):

    i = pos - 1

    while i >= 0 and text[i].isspace():
        i -= 1

    return i >= 0 and (text[i] == '(' or text[i] == ',')


def compute_scope_ranges(text):

    stack = []
    scopes = []

    for i, ch in enumerate(text):

        if ch == "{":
            stack.append(i)

        elif ch == "}":
            if stack:
                start = stack.pop()
                scopes.append((start, i))

    return scopes


# def find_minimal_scope(scopes, pos):

#     for start, end in reversed(scopes):

#         if start < pos < end:
#             return (start, end)

#     return None


def find_scope_stack(scopes, pos):

    return [
        (start, end)
        for start, end in scopes
        if start < pos < end
    ]


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


def parse_definitions_from_content(content, pos=0, source_file=None, entry_scope="", external=False, friend=False):

    function_entries = []
    variable_entries = []

    filtered_content = remove_strings_preserve_length(remove_comments_preserve_length(content))

    scopes = compute_scope_ranges(filtered_content)
    scope_stack = find_scope_stack(scopes, pos)

    for match in USER_DEFINED_FUNC_TASK_SUB_REGEX.finditer(content):

        if content[match.start()] != filtered_content[match.start()]:
            continue

        function_scope_stack = find_scope_stack(scopes, match.start())
        minimal_scope = function_scope_stack[0] if (function_scope_stack and len(function_scope_stack) > 0) else None

        if minimal_scope is not None and minimal_scope not in scope_stack:
            continue

        name = match.group("name")
        kind = match.group("kind")
        rtype = match.group("rtype")

        if not rtype:
            rtype = "void" if kind in ("task", "sub") else "unspecified"

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

        line_number = content.count("\n", 0, match.start()) + 1 + raw_doc.count("\n") + (1 if match.group("doc") else 0)

        function_entry = {
            "scope": entry_scope,
            "trigger": name,
            "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
            "params": param_names,
            "param_types": param_types,
            "return_type": rtype,
            "doc": doc,
            "language": "User Defined",
            "source_file": source_file,
            "line_number": line_number
        }

        if external:
            function_entry["external"] = True

        if friend:
            function_entry["friend"] = True

        function_entries.append(function_entry)

        brace_pos = filtered_content.find("{", match.end())
        parameter_scope_stack = find_scope_stack(scopes, brace_pos + 1)
        minimal_parameter_scope = parameter_scope_stack[0] if (parameter_scope_stack and len(parameter_scope_stack) > 0) else None

        if minimal_parameter_scope is not None and minimal_parameter_scope in scope_stack and pos <= minimal_parameter_scope[1]:
            name_type = "non-task"

            if len(name) > 0 and name[0] == "_":
                name_type = "task"
            elif len(name) > 2 and name[0:3] == "Obj":
                name_type = "obj-func"

            for i, (param_name, param_type) in enumerate(zip(param_names, param_types)):
                variable_entry = {
                    "scope": entry_scope,
                    "trigger": param_name,
                    "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
                    "type": param_type,
                    "value": "<span style=\"color: hsl(261, 100%, 75%);\">Parameter {}</span> of <span style=\"color: {};\">{}</span>".format(i + 1, NAME_COLORS.get(name_type, "#40CEDF"), name),
                    "doc": "",
                    "language": "User Defined",
                    "source_file": source_file,
                    "line_number": line_number
                }

                if external:
                    variable_entry["external"] = True

                if friend:
                    variable_entry["friend"] = True

                variable_entries.append(variable_entry)

    seen_parameters = [entry["trigger"] for entry in variable_entries]

    for match in USER_DEFINED_VARIABLE_REGEX.finditer(content):

        if content[match.start()] != filtered_content[match.start()]:
            continue

        matchName1 = match.group("name1")
        name = matchName1 if matchName1 else match.group("name2")

        if name in seen_parameters:
            continue

        if preceded_by_paren_or_comma(content, match.start()):
            brace_pos = filtered_content.find("{", match.end())
            var_scope_stack = find_scope_stack(scopes, brace_pos + 1)
            minimal_scope = var_scope_stack[0] if (var_scope_stack and len(var_scope_stack) > 0) else None

        else:
            var_scope_stack = find_scope_stack(scopes, match.start())
            minimal_scope = var_scope_stack[0] if (var_scope_stack and len(var_scope_stack) > 0) else None

        if minimal_scope is not None and minimal_scope not in scope_stack:
            continue

        if minimal_scope is not None and pos > minimal_scope[1]:
            continue

        # omit variable definitions in viewed file past cursor (variables only, not functions)

        if len(entry_scope) > 0 and match.start() > pos:
            continue

        type = ("const {}".format(match.group("type1"))) if matchName1 else match.group("type2")

        raw_doc = match.group("doc") or "No documentation."
        doc = raw_doc.strip()

        value = remove_comments_and_trim(match.group("value").strip()).replace("\n", "<br>").replace("\t", "&emsp;&emsp;") if match.group("value") else "not initialized"

        line_number = content.count("\n", 0, match.start()) + 1 + raw_doc.count("\n") + (1 if match.group("doc") else 0)

        variable_entry = {
            "scope": entry_scope,
            "trigger": name,
            "namespace": "{}::".format(os.path.splitext(os.path.basename(source_file))[0]),
            "type": type,
            "value": "<span style=\"color: #A0A070;\">{}</span>".format(value),
            "doc": doc,
            "language": "User Defined",
            "source_file": source_file,
            "line_number": line_number
        }

        if external:
            variable_entry["external"] = True

        if friend:
            variable_entry["friend"] = True

        variable_entries.append(variable_entry)

    return function_entries, variable_entries, scopes, scope_stack


def extract_user_definitions(view, file_path, location=None):

    global _user_included_definitions_cache

    file_path = os.path.abspath(file_path)

    if not file_path.lower().endswith(".dnh"):
        return [], []

    visited = set()

    functions = []
    variables = []

    def extract_user_definitions_recurse(file_path, offset=None, inclusion_root=None, caching=False, friend=False):

        if file_path in visited:
            return

        visited.add(file_path)

        if not os.path.exists(file_path):
            return

        is_view_file = False

        if os.path.abspath(view.file_name()) == file_path:
            content = view.substr(sublime.Region(0, view.size()))
            is_view_file = True

        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                return

        internal_functions, internal_variables, scopes, scope_stack = parse_definitions_from_content(
            content,
            pos=offset if offset else 0,
            source_file=file_path,
            entry_scope=view.scope_name(0) if os.path.abspath(view.file_name()) == file_path else "",
            friend=friend
        )

        functions.extend(internal_functions)
        variables.extend(internal_variables)

        if caching:
            if inclusion_root in _user_included_definitions_cache:
                _user_included_definitions_cache[inclusion_root][0].extend(internal_functions)
                _user_included_definitions_cache[inclusion_root][1].extend(internal_variables)
            else:
                _user_included_definitions_cache[inclusion_root] = (internal_functions, internal_variables)

        for match in INCLUDE_REGEX.finditer(remove_comments(content)):

            if offset and match.start() > offset:
                continue

            include_scope_stack = find_scope_stack(scopes, match.start())
            minimal_scope = include_scope_stack[0] if (include_scope_stack and len(include_scope_stack) > 0) else None

            if minimal_scope is not None and minimal_scope not in scope_stack:
                continue

            relative_path = match.group(1)
            included_file = resolve_include(file_path, relative_path)

            if included_file in _user_included_definitions_cache:
                downward_functions, downward_variables = _user_included_definitions_cache[included_file]

                functions.extend(downward_functions)
                variables.extend(downward_variables)

            else:
                extract_user_definitions_recurse(included_file, inclusion_root=(included_file if is_view_file else inclusion_root), caching=True, friend=friend)

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

            if included_file in _user_included_definitions_cache:
                downward_functions, downward_variables = _user_included_definitions_cache[included_file]

                functions.extend(downward_functions)
                variables.extend(downward_variables)

            else:
                extract_user_definitions_recurse(included_file, inclusion_root=included_file, caching=True, friend=True)

    extract_user_definitions_recurse(file_path, offset=location)

    return functions, variables


def extract_user_definitions_everywhere(file_path):

    functions = []
    variables = []

    dnh_files = get_dnh_files(file_path)

    for dnh_file in dnh_files:

        if file_path == dnh_file:
            continue

        try:
            with open(dnh_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        internal_functions, internal_variables, _, _ = parse_definitions_from_content(
            content,
            pos=0,
            source_file=dnh_file,
            external=True
        )

        functions.extend(internal_functions)
        variables.extend(internal_variables)

    return functions, variables


def get_call_argument_info(view, name_region):

    open_paren = name_region.end()

    if view.substr(open_paren) != '(':
        return None

    depth = 0
    comma_count = 0
    i = open_paren + 1
    size = view.size()

    while i < size:

        ch = view.substr(i)

        if ch == '(':
            depth += 1

        elif ch == ')':
            if depth == 0:
                break
            depth -= 1

        elif ch == ',' and depth == 0:
            comma_count += 1

        i += 1

    if i == open_paren + 1:
        return 0

    return comma_count + 1


def extract_call_arguments(view, name_region):

    open_paren = name_region.end()

    if view.substr(open_paren) != '(':
        return []

    args = []
    depth = 0
    start = open_paren + 1
    i = start
    size = view.size()

    while i < size:

        ch = view.substr(i)

        if ch == '(':
            depth += 1

        elif ch == ')':
            if depth == 0:
                args.append(view.substr(sublime.Region(start, i)).strip())
                break
            depth -= 1

        elif ch == ',' and depth == 0:
            args.append(view.substr(sublime.Region(start, i)).strip())
            start = i + 1

        i += 1

    return args


def get_expression_context(view, name_region):
    line = view.substr(view.line(name_region))
    before = line[:name_region.begin() - view.line(name_region).begin()]

    if "=" in before:
        return "assignment"

    return "expression"


def score_return_context(entry, context):

    return_type = entry.get("return_type")

    if context == "assignment":
        if return_type == "void":
            return -100000
        return 20000

    if context == "expression":
        if return_type == "void":
            return 20000
        return 10000

    return 0


def normalize_name(name):

    return re.sub(r'[^a-z0-9]', '', name.lower())


def score_similarity(a, b):

    if a == b:
        return 75

    if a in b or b in a:
        return 50

    a = normalize_name(a)
    b = normalize_name(b)

    match = SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))

    if match.size < 3:
        return 0

    return match.size * 2 + int(match.size / max(len(a), 1) * 5)


def score_param_alignment(entry, call_args):

    param_names = entry["params"]
    score = 0

    for arg, param in zip(call_args, param_names):

        norm_arg = normalize_name(arg)
        norm_param = normalize_name(param)

        score += score_similarity(norm_arg, norm_param)

    return score


def choose_best_overload(matching, arg_count, context, call_args):

    if not matching:
        return (None, [])

    candidates = []

    for (ind, e) in enumerate(matching):

        param_len = len(e["params"])
        is_variadic = e.get("is_variadic", False)
        fixed_count = e.get("fixed_param_count", param_len)

        score = 0

        if not is_variadic:
            if arg_count == param_len:
                score += 10000
            else:
                continue

        else:
            if arg_count < fixed_count:
                continue

            if arg_count == fixed_count:
                score += 2000
            else:
                score += 1000

        score += score_return_context(e, context)
        score += score_param_alignment(e, call_args)

        candidates.append((score, e, ind))

    if not candidates:
        return (None, [])

    candidates.sort(key=lambda x: x[0], reverse=True)

    return (candidates[0][1], candidates)


def open_file_center_and_highlight(href):

    path_line, _ = href.rsplit(":", 1)
    file_path, line_number = path_line.rsplit(":", 1)
    line_number = int(line_number)

    window = sublime.active_window()

    view = window.open_file(file_path)

    def focus_when_ready():
        if view.is_loading():
            sublime.set_timeout(focus_when_ready, 10)
            return

        pt = view.text_point(line_number - 1, 0)
        line_region = view.full_line(pt)

        visible = view.visible_region()

        if not visible.contains(pt):
            view.sel().clear()
            view.sel().add(sublime.Region(pt))
            view.show_at_center(pt)

        view.add_regions(
            "hover_highlight",
            [line_region],
            scope="region.bluish",
            flags=sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE
        )

    focus_when_ready()


class HoverEventListener(sublime_plugin.EventListener):

    def on_text_command(self, view, command_name, args):

        if command_name in ("drag_select", "left_delete", "right_delete"):
            view.erase_regions(HIGHLIGHT_KEY)

    def on_post_save(self, view):

        global _user_included_definitions_cache

        _user_included_definitions_cache = {}

        extract_user_definitions(view, view.file_name(), view.sel()[0].begin())

    def on_activated(self, view):

        global _user_included_definitions_cache

        _user_included_definitions_cache = {}

        extract_user_definitions(view, view.file_name(), view.sel()[0].begin())


class Library:

    def __init__(self):

        self.collection = []
        self.settings = None
        self.file_list = []

    def load(self):

        self.collection = []

        self.settings = sublime.load_settings(
            "sublime-completions-library.sublime-settings"
        )
        self.file_list = self.settings.get("completions_file_list", [])

        for filename in self.file_list:
            settings = sublime.load_settings(filename)
            parsed = self.dictionaryize(settings)
            if parsed:
                self.collection.append(parsed)

    def dictionaryize(self, settings):

        scope = settings.get("scope")
        raw_entries = settings.get("dict")

        if not scope or not raw_entries:
            return None

        entries = []

        for entry in raw_entries:
            lang = entry.get("lang")
            sig = entry.get("sig")
            doc = entry.get("doc", "No documentation.")
            type_str = entry.get("type")

            if not sig or not type_str:
                continue

            match = ENGINE_FUNC_REGEX.match(sig)
            if not match:
                continue

            if len(doc) == 0:
                doc = "No documentation."

            namespace = match.group(1) or ""
            name = match.group(2)
            params_raw = match.group(3)

            if params_raw.strip():
                param_names = [p.strip() for p in params_raw.split(",")]
            else:
                param_names = []

            for i, p in enumerate(param_names):
                if len(p) > 0 and p[-1] != '.':
                    param_names[i] = p + "_"

            type_tokens = type_str.split()

            if len(type_tokens) != len(param_names) + 1:
                continue

            for i, type_token in enumerate(type_tokens):
                type_tokens[i] = type_token.replace('-', ' ')

                if type_token[:4] == "real":
                    bracket_count = type_token.count('[')
                    brack = "[]" * bracket_count
                    type_tokens[i] = type_token + " { int" + brack + ", float" + brack + " }"


            param_types = type_tokens[:-1]
            return_type = type_tokens[-1]

            entries.append({
                "scope": scope,
                "trigger": name,
                "language": lang,
                "namespace": namespace,
                "params": param_names,
                "param_types": param_types,
                "return_type": return_type,
                "doc": doc,
                "is_variadic": any(p.endswith("..") for p in param_types),
                "fixed_param_count": sum(1 for p in param_types if not p.endswith(".."))
            })

        return {
            "scope": scope,
            "entries": entries
        }


class DictCollector(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):

        if not library.collection:
            return None

        location = locations[0]
        items = []

        for lib in library.collection:

            scope = lib["scope"]

            if not view.match_selector(location, scope):
                continue

            for entry in lib["entries"]:

                plain_params = ", ".join(entry["params"])

                snippet = "{}({});".format(
                    entry["trigger"],
                    plain_params
                )

                annotation = entry["return_type"]

                signature = "%s%s(%s)" % (
                    entry["namespace"],
                    entry["trigger"],
                    ", ".join(entry["params"])
                )

                return_type = entry["return_type"]

                doc_lines = entry["doc"].split("\n")

                doc_html = "<div>{}</div>".format(doc_lines[0])

                language = "<i>{}</i>".format(entry["language"])

                details = """
                <div>
                    <div>{}&emsp;<b>{}</b> <span style="opacity:0.6;">→ {}</span></div>
                    <div style="margin-top:6px;"></div>
                    {}
                </div>
                """.format(language, signature, return_type, doc_html)

                full_trigger = "{}{}".format(
                    entry["namespace"],
                    entry["trigger"]
                )

                items.append(
                    sublime.CompletionItem(
                        trigger=full_trigger,
                        annotation=annotation,
                        completion=snippet,
                        details=details,
                        kind=sublime.KIND_FUNCTION
                    )
                )

            file_path = view.file_name()
            user_function_entries, user_variable_entries = extract_user_definitions(view, file_path, location)

            for entry in user_function_entries:

                snippet = "{}({});".format(
                    entry["trigger"],
                    ", ".join(entry["params"])
                )

                signature = "{}{}({})".format(
                    entry["namespace"],
                    entry["trigger"],
                    ", ".join(entry["params"])
                )

                doc_lines = entry["doc"].split("\n")
                doc_html = "<div>{}</div>".format(doc_lines[0]) if doc_lines else ""

                details = """
                <div>
                    <div><b>{}</b> <span style="opacity:0.6;">→ {}</span></div>
                    <div style="margin-top:6px;"></div>
                    {}
                </div>
                """.format(signature, entry["return_type"], doc_html)

                full_trigger = "{}{}{}".format(
                    "friend." if entry.get("friend") else "",
                    entry["namespace"],
                    entry["trigger"]
                )

                items.append(
                    sublime.CompletionItem(
                        trigger=full_trigger,
                        annotation=entry["return_type"],
                        completion=snippet,
                        details=details,
                        kind=sublime.KIND_FUNCTION
                    )
                )

            for non_function in ENGINE_NON_FUNCTIONS:

                name = non_function.get("sig")
                language = non_function.get("lang", "Unspecified Language")
                completion = non_function.get("completion", name)
                description = non_function.get("desc", name)

                details = "<i>&emsp;{}&emsp;{}</i>".format(language, html.escape(description))

                items.append(
                    sublime.CompletionItem(
                        trigger=name,
                        annotation="",
                        completion=completion,
                        completion_format=sublime.COMPLETION_FORMAT_SNIPPET,
                        details=details,
                        kind=non_function.get("kind", sublime.KIND_VARIABLE)
                    )
                )

            for entry in user_variable_entries:

                snippet = "{}".format(
                    entry["trigger"]
                )

                doc_lines = entry["doc"].split("\n")
                doc_html = "<div>{}</div>".format(doc_lines[0]) if doc_lines else ""

                details = "<i>&emsp;User Defined</i>&emsp;({})&emsp;<i>{}</i>".format(entry["value"], doc_html)

                full_trigger = "{}{}{}".format(
                    "friend." if entry.get("friend") else "",
                    entry["namespace"],
                    entry["trigger"]
                )

                items.append(
                    sublime.CompletionItem(
                        trigger=full_trigger,
                        annotation=entry["type"],
                        completion=snippet,
                        details=details,
                        kind=sublime.KIND_VARIABLE
                    )
                )

        if not items:
            return None

        return sublime.CompletionList(
            items,
            sublime.INHIBIT_WORD_COMPLETIONS
            | sublime.INHIBIT_EXPLICIT_COMPLETIONS
            | sublime.DYNAMIC_COMPLETIONS
            | sublime.INHIBIT_REORDER)


class DnhHoverDocs(sublime_plugin.EventListener):

    def on_hover(self, view, point, hover_zone):

        if hover_zone != sublime.HOVER_TEXT:
            return

        if not library.collection:
            return

        for lib in library.collection:

            scope = lib.get("scope")

            if not scope:
                continue

            if not view.match_selector(point, scope):
                continue

            word_region = view.expand_by_class(
                point,
                sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
            )

            word = view.substr(word_region).strip()

            if not word:
                continue

            matching = []

            file_path = view.file_name()

            can_match_multiple = False

            if "//// external dependency" in view.substr(view.full_line(point)):
                can_match_multiple = True
                user_function_entries, user_variable_entries = extract_user_definitions_everywhere(file_path)

            else:
                user_function_entries, user_variable_entries = extract_user_definitions(view, file_path, point)

            all_entries = lib.get("entries", []) + user_function_entries + user_variable_entries + ENGINE_TRIGGERS

            for entry in all_entries:
                if entry["trigger"] == word:
                    matching.append(entry)

            if not matching:
                return

            arg_count = get_call_argument_info(view, word_region)

            if arg_count is not None:

                # Find out which overload to show the docs for based on argument count
                # Some ph3 vs ph3sx function differences don't change function signature, rely on argument naming convention

                context = get_expression_context(view, word_region)
                call_args = extract_call_arguments(view, word_region)

                if can_match_multiple:                    
                    _, candidates = choose_best_overload(matching, arg_count, context, call_args)

                    if len(candidates) > 0:
                        merge_candidate = candidates[0][1]

                        merge_candidate["source_files"] = [merge_candidate["source_file"]]
                        merge_candidate["line_numbers"] = [merge_candidate["line_number"]]

                        del merge_candidate["source_file"]
                        del merge_candidate["line_number"]

                        if "namespace" in merge_candidate:
                            del merge_candidate["namespace"]

                        for other_candidate in candidates[1:]:

                            merge_candidate["source_files"].append(other_candidate[1]["source_file"])
                            merge_candidate["line_numbers"].append(other_candidate[1]["line_number"])

                            if other_candidate[1]["doc"] != "No documentation.":
                                merge_candidate["doc"] += "\n" + other_candidate[1]["doc"]

                        self.show_popup(view, word_region, merge_candidate)

                else:
                    best, _ = choose_best_overload(matching, arg_count, context, call_args)

                    if best:
                        self.show_popup(view, word_region, best)
                        return


            self.show_popup(view, word_region, matching[0])


    def show_popup(self, view, region, entry):

        def popup_link_clicked(href):

            open_file_center_and_highlight(href)
            sublime.active_window().open_file(href, sublime.ENCODED_POSITION)

        language_colors = {
            "ph3": "deepskyblue",
            "ph3sx": "hotpink",
            "ph3sx-zlabel": "crimson",
            "User Defined": "lightgoldenrodyellow"
        }

        language = entry["language"]

        source_html = ""

        source_file = entry.get("source_file")
        source_files = entry.get("source_files")

        if source_file:
            line_number = entry.get("line_number")
            source_html = "<a href=\"{}\">{}:{}</a>".format("{}:{}:0".format(source_file, line_number), source_file, line_number)

        elif source_files:
            line_numbers = entry.get("line_numbers")

            for src_file, line_num in zip(source_files, line_numbers):
                source_html += "<a href=\"{}\">{}:{}</a><br>".format("{}:{}:0".format(src_file, line_num), src_file, line_num)


        wrapped_lines = []

        for line in entry.get("doc", "").split("\n"):
            wrapped_lines.extend(textwrap.wrap(line, width=9000) or [""])

        doc_html = "".join(
            "<div style='margin-bottom: 4px; color: #A0A070;'><i>{}</i></div>".format(html.escape(line))
            for line in wrapped_lines
        )

        location_html = "<span style=\"color: gainsboro;\"><br>{}</span>".format(source_html) if len(source_html) > 0 else ""

        if "return_type" in entry:
            # Functions

            return_type = entry["return_type"]

            param_zip = zip(entry["params"], entry["param_types"])

            param_html = "".join(
                "<br>&emsp;&emsp;<span style=\"color: #FF6030;\">{}</span>, : <span style=\"color: #40D0B0;\"><i>{}</i></span>".format(html.escape(name), html.escape(ptype))
                for name, ptype in param_zip
            ) + ("<br>" if len(entry["params"]) > 0 else "")

            trig = entry["trigger"]

            name_type = "non-task"

            if len(trig) > 0 and trig[0] == "_":
                name_type = "task"
            elif len(trig) > 2 and trig[0:3] == "Obj":
                name_type = "obj-func"

            html_content = """
            <div style="padding: 10px;">
                <div style="font-size: 0.875rem; margin-bottom: 4px;">
                    <span style="opacity:0.6; color: {language_color};"><i>{language}{location}</i></span>
                </div>
                <div style="font-size: 1.05rem; margin-bottom: 6px;">
                    <span style="opacity:0.6;color: #AFFFC0;">{access}</span>
                    <span style="opacity:0.6;color: violet;">{namespace}</span>{name}({params})
                     → <span style="color: #40D0B0;"><i>{rtype}</i></span>
                </div>
                <hr>
                {doc}
            </div>
            """.format(
                language_color=html.escape(language_colors.get(language, "white")),
                language=html.escape(language),
                access="friend " if entry.get("friend") else "",
                namespace=html.escape(entry.get("namespace", "")),
                name="<span style=\"color: " + NAME_COLORS.get(name_type, "#40CEDF") + ";\">" + html.escape(entry["trigger"]) + "</span>",
                params=param_html,
                rtype=html.escape(return_type),
                doc=doc_html,
                location=location_html
            )

        else:
            # Variables

            trig = entry["trigger"]

            name_type = ""

            if (len(trig) > 0):
                if trig[0] == "_":
                    name_type = "global-variable"
                elif trig[-1] == "_":
                    name_type = "param-variable"
                elif trig.isupper() and trig in ENGINE_SIGS:
                    name_type = "constant"
                elif trig.isupper():
                    name_type = "user-constant"

            html_content = """
            <div style="padding: 10px;">
                <div style="font-size: 0.875rem; margin-bottom: 4px;">
                    <span style="opacity:0.6; color: {language_color};"><i>{language}{location}</i></span>
                </div>
                <div style="font-size: 1.05rem; margin-bottom: 6px;">
                    <span style="opacity:0.6;color: #AFFFC0;">{access}</span>
                    <span style="color: #40D0B0;"><i>{type}</i></span>
                     <span style="opacity:0.6;color: violet;">{namespace}</span>{name}   {value}
                </div>
                <hr>
                {doc}
            </div>
            """.format(
                language_color=html.escape(language_colors.get(language, "white")),
                language=html.escape(language),
                access="friend " if entry.get("friend") else "",
                namespace=entry.get("namespace", ""),
                type=html.escape(entry["type"]),
                name="<span style=\"color: " + NAME_COLORS.get(name_type, "#90B0D0") + ";\">" + html.escape(entry["trigger"]) + "</span>",
                value="({})".format(entry.get("value")) if entry.get("value") else "",
                doc=doc_html,
                location=location_html
            )

        viewport_width, viewport_height = view.viewport_extent()

        popup_max_width = int(viewport_width)

        view.show_popup(
            html_content,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=view.line(region).begin(),
            max_width=popup_max_width,
            max_height=500,
            on_navigate=popup_link_clicked
        )


library = Library()


def plugin_loaded():
    library.load()
