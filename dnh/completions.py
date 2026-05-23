import sublime
import sublime_plugin
import re
import html
import textwrap
import os
import threading
from difflib import SequenceMatcher

from . import statements as st

SUBLIME_KINDS = [
    sublime.KIND_AMBIGUOUS,
    sublime.KIND_KEYWORD,
    sublime.KIND_TYPE,
    sublime.KIND_FUNCTION,
    sublime.KIND_NAMESPACE,
    sublime.KIND_NAVIGATION,
    sublime.KIND_MARKUP,
    sublime.KIND_VARIABLE,
    sublime.KIND_SNIPPET
]

HIGHLIGHT_KEY = "hover_highlight"

_completion_cache = None
_completion_timer = None


def _build_completions(view, location):
    global _completion_cache

    if not library.collection:
        return

    items = []

    for lib in library.collection:

        scope = lib["scope"]

        if not view.match_selector(location, scope):
            continue

        for entry in lib["entries"]:

            plain_params = ", ".join(entry["params"])

            snippet = "{}({})".format(
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

            language_shorthands = entry["language"].split(" ")

            language = "<i>{}</i>".format(" | ".join([st.ENGINE_SHORTHANDS[l] for l in language_shorthands]))

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
        user_function_entries, user_variable_entries, _ = st.extract_user_definitions(file_path, view.substr(sublime.Region(0, view.size())), view.scope_name(0), location)

        for entry in user_function_entries:

            snippet = "{}({})".format(
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

        for non_function in st.ENGINE_NON_FUNCTIONS:

            name = non_function.get("sig")

            language = "Unspecified Language"
            if "lang" in non_function:
                language_shorthands = non_function["lang"].split(" ")
                language = " | ".join([st.ENGINE_SHORTHANDS[l] for l in language_shorthands])

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
                    kind=SUBLIME_KINDS[non_function.get("kind", 7)]
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
        return

    _completion_cache = sublime.CompletionList(
        items,
        sublime.INHIBIT_WORD_COMPLETIONS
        | sublime.INHIBIT_EXPLICIT_COMPLETIONS
        | sublime.DYNAMIC_COMPLETIONS
        | sublime.INHIBIT_REORDER)


# def get_call_argument_info(view, name_region):
#     open_paren = name_region.end()

#     if view.substr(open_paren) != '(':
#         return None

#     depth = 0
#     comma_count = 0
#     i = open_paren + 1
#     size = view.size()

#     while i < size:

#         ch = view.substr(i)

#         if ch == '(' or ch == '[':
#             depth += 1

#         elif ch == ')' or ch == ']':
#             if depth == 0:
#                 break
#             depth -= 1

#         elif ch == ',' and depth == 0:
#             comma_count += 1

#         i += 1

#     if i == open_paren + 1:
#         return 0

#     return comma_count + 1


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

        if ch == '(' or ch == '[':
            depth += 1

        elif ch == ')' or ch == ']':
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
    # doesn't account for multiline assignment

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
        pass
        # st.clear_cache()
        # st.extract_user_definitions(view.file_name(), view.substr(sublime.Region(0, view.size())), view.scope_name(0), view.sel()[0].begin())

    def on_activated(self, view):
        pass
        # st.clear_cache()
        # st.extract_user_definitions(view.file_name(), view.substr(sublime.Region(0, view.size())), view.scope_name(0), view.sel()[0].begin())


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

            match = st.ENGINE_FUNC_REGEX.match(sig)
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
        global _completion_cache

        if _completion_cache is None:
            _build_completions(view, locations[0])

        return _completion_cache

    def on_post_save(self, view):
        global _completion_cache

        if view.match_selector(0, "source.dnh"):
            st.clear_cache()
            threading.Thread(target=_build_completions, args=(view, view.sel()[0].begin(),), daemon=True).start()

    def on_modified(self, view):
        global _completion_cache
        global _completion_timer

        if not view.match_selector(0, "source.dnh"):
            return
        
        if _completion_timer is not None:
            _completion_timer.cancel()
        
        _completion_timer = threading.Timer(
            st.DEBOUNCE_TIME,
            lambda: threading.Thread(target=_build_completions, args=(view, view.sel()[0].begin(),), daemon=True).start()
        )
        _completion_timer.start()

    def on_activated(self, view):
        global _completion_cache

        if view.match_selector(0, "source.dnh"):
            threading.Thread(target=_build_completions, args=(view, view.sel()[0].begin(),), daemon=True).start()

        else:
            _completion_cache = None


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
                user_function_entries, user_variable_entries, _ = st.extract_user_definitions_everywhere(file_path)

            else:
                user_function_entries, user_variable_entries, _ = st.extract_user_definitions(file_path, view.substr(sublime.Region(0, view.size())), view.scope_name(0), point)

            all_entries = lib.get("entries", []) + user_function_entries + user_variable_entries + st.ENGINE_TRIGGERS

            for entry in all_entries:
                if entry["trigger"] == word:
                    matching.append(entry)

            if not matching:
                return

            # arg_count = get_call_argument_info(view, word_region)
            arg_count = st.get_call_argument_info(view.substr(sublime.Region(word_region.end(), view.size())).lstrip())

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

                        if len(candidates) > 1:
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

            else:

                # Variable

                if can_match_multiple:
                    merge_candidate = matching[0]

                    merge_candidate["source_files"] = [merge_candidate["source_file"]]
                    merge_candidate["line_numbers"] = [merge_candidate["line_number"]]

                    merge_candidate["value"] = "<br>{} {}".format(merge_candidate["value"], os.path.basename(merge_candidate["source_file"]))

                    del merge_candidate["source_file"]
                    del merge_candidate["line_number"]

                    if "namespace" in merge_candidate:
                        del merge_candidate["namespace"]

                    if len(matching) > 1:
                        for other_candidate in matching[1:]:

                            merge_candidate["source_files"].append(other_candidate["source_file"])
                            merge_candidate["line_numbers"].append(other_candidate["line_number"])
                            merge_candidate["value"] += ",<br>{} {}".format(other_candidate["value"], os.path.basename(other_candidate["source_file"]))

                            if other_candidate["doc"] != "No documentation.":
                                merge_candidate["doc"] += "\n" + other_candidate["doc"]

                    merge_candidate["value"] += "<br>"

                    self.show_popup(view, word_region, merge_candidate)

                else:
                    # find match in matching with deepest scope stack
                    deepest_match = max(matching, key=lambda m: len(m.get("scope_stack", [])))
                    self.show_popup(view, word_region, deepest_match)


    def show_popup(self, view, region, entry):

        def popup_link_clicked(href):

            open_file_center_and_highlight(href)
            sublime.active_window().open_file(href, sublime.ENCODED_POSITION)

        language_colors = {
            st.ENGINE_LANGUAGES[0]: "deepskyblue",
            st.ENGINE_LANGUAGES[1]: "hotpink",
            st.ENGINE_LANGUAGES[2]: "crimson",
            "User Defined": "lightgoldenrodyellow"
        }

        language = entry["language"]

        language_html = ""

        for language_shorthand in language.split(" "):

            if language_shorthand not in st.ENGINE_SHORTHANDS:
                continue

            language_html += """
            {separator} <span style="color: {language_color};">{displayed_language}</span>
            """.format(
                language_color=html.escape(language_colors.get(language_shorthand, "white")),
                displayed_language=html.escape(st.ENGINE_SHORTHANDS[language_shorthand]),
                separator="|" if language_html != "" else ""
            )

        if language_html == "":
            language_html += """
            <span style="color: {language_color};">{displayed_language}</span>
            """.format(
                language_color=html.escape(language_colors.get(language, "white")),
                displayed_language=html.escape(language)
            )

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
                    <i>{language}{location}</i>
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
                language=language_html,
                access="friend " if entry.get("friend") else "",
                namespace=html.escape(entry.get("namespace", "")),
                name="<span style=\"color: " + st.NAME_COLORS.get(name_type, "#40CEDF") + ";\">" + html.escape(entry["trigger"]) + "</span>",
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
                elif trig.isupper() and trig in st.ENGINE_SIGS:
                    name_type = "constant"
                elif trig.isupper():
                    name_type = "user-constant"

            html_content = """
            <div style="padding: 10px;">
                <div style="font-size: 0.875rem; margin-bottom: 4px;">
                    <i>{language}{location}</i>
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
                language=language_html,
                access="friend " if entry.get("friend") else "",
                namespace=entry.get("namespace", ""),
                type=html.escape(entry["type"]),
                name="<span style=\"color: " + st.NAME_COLORS.get(name_type, "#90B0D0") + ";\">" + html.escape(entry["trigger"]) + "</span>",
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


HEX_REGEX = re.compile(
    r'\b0x([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})\b'
)


def hex_to_css(hex_value, invert=False):

    if len(hex_value) == 6:
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        a = 1.0

    else:
        r = int(hex_value[2:4], 16)
        g = int(hex_value[4:6], 16)
        b = int(hex_value[6:8], 16)
        a = int(hex_value[0:2], 16) / 255.0

    r = (255 - r) if invert else r
    g = (255 - g) if invert else g
    b = (255 - b) if invert else b

    return f"rgb({r}, {g}, {b} / {a:.3f})", r, g, b, a


class HexColorSwatchListener(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        return settings.get("syntax", "").endswith("ph3sx.sublime-syntax")

    def __init__(self, view):
        super().__init__(view)

        self.phantom_set = sublime.PhantomSet(
            view,
            "hex_color_swatches"
        )

    def on_load_async(self):
        self.update_swatches()

    def on_modified_async(self):
        self.update_swatches()

    def on_activated_async(self):
        self.update_swatches()

    def update_swatches(self):

        content = self.view.substr(sublime.Region(0, self.view.size()))

        phantoms = []

        for match in HEX_REGEX.finditer(content):

            hex_value = match.group(1)

            css, _, _, _, hex_alpha = hex_to_css(hex_value)
            css_invert, _, _, _, _ = hex_to_css(hex_value, True)

            region = sublime.Region(match.end(), match.end())

            alpha_width = int(12 * hex_alpha)

            html = """
                <body>
                    <div style="
                        width: 12px;
                        height: 12px;
                        border: 1px solid #888888;
                        padding: 2px;
                        background-color: {css};
                    ">
                        <div style="
                            width: {alpha_width}px;
                            height: 1.5px;
                            background-color: {css_invert};
                        ">
                        </div>
                    </div>
                </body>
            """.format(css=css, css_invert=css_invert, alpha_width=alpha_width)

            phantoms.append(
                sublime.Phantom(
                    region,
                    html,
                    sublime.LAYOUT_INLINE
                )
            )

        self.phantom_set.update(phantoms)


library = Library()


def plugin_loaded():
    library.load()
