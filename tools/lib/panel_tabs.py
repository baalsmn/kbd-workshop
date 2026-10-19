# KiKit plugins for the assembly panels (see tools/panel.sh, <keyboard>/panel.json).
#
# FixedTabs (tabs plugin): breakaway tabs at fixed positions along the board's
# bounding box. KiKit's own tab layouts space tabs along the bounding box, which on
# an outline like hachigo74's (angled halves, thumb keys hanging lower) gives tabs
# into the middle of nowhere; here each tab sits where the outline reaches the frame.
#   "tabs": {"type": "plugin", "code": "tools/lib/panel_tabs.py.FixedTabs",
#            "arg": "width 5; top 51.6 166.4:8; bottom 126.6; left 86; right 86",
#            "fillet": "1mm"}
#   top / bottom: x in mm from the bbox's left edge; left / right: y in mm from the
#   bbox's top edge. A tab starts at the bbox edge and runs inwards until it meets the
#   outline, then out to the frame. "value:w" gives that tab its own width (e.g. the
#   long bridges to a recessed edge are made wider); "width" is the default.
#
# RailsFrame (framing plugin): a closed frame with its own width for the top / bottom
# rails (which carry the fiducials and tooling holes, so JLC's fiducial clearance
# sets their width) and for the side rails (support only, JLC's 5 mm minimum).
#   "framing": {"type": "plugin", "code": "tools/lib/panel_tabs.py.RailsFrame",
#               "arg": "rails 9; sides 5; space 2"}
from kikit.plugin import TabsPlugin, FramingPlugin
from kikit.annotations import TabAnnotation
from kikit.common import fromMm
from kikit.substrate import Substrate
from shapely.geometry import box


def parse(arg, keys):
    spec = {k: [] for k in keys}
    for part in arg.split(';'):
        words = part.split()
        if not words: continue
        if words[0] not in spec: raise RuntimeError('panel_tabs: unknown key %r in %r' % (words[0], arg))
        spec[words[0]] = words[1:]
    return spec


class FixedTabs(TabsPlugin):
    def buildTabAnnotations(self, panel):
        spec = parse(self.userArg, ('width', 'top', 'bottom', 'left', 'right'))
        default = float(spec['width'][0]) if spec['width'] else 5.0
        def items(key):
            for w in spec[key]:
                v, _, wd = w.partition(':')
                yield float(v), float(wd) if wd else default
        for s in panel.substrates:
            minx, miny, maxx, maxy = s.bounds()
            for x, w in items('top'):
                s.annotations.append(TabAnnotation(None, (minx + fromMm(x), miny), (0, 1), fromMm(w)))
            for x, w in items('bottom'):
                s.annotations.append(TabAnnotation(None, (minx + fromMm(x), maxy), (0, -1), fromMm(w)))
            for y, w in items('left'):
                s.annotations.append(TabAnnotation(None, (minx, miny + fromMm(y)), (1, 0), fromMm(w)))
            for y, w in items('right'):
                s.annotations.append(TabAnnotation(None, (maxx, miny + fromMm(y)), (-1, 0), fromMm(w)))


class RailsFrame(FramingPlugin):
    def _sizes(self):
        spec = parse(self.userArg, ('rails', 'sides', 'space'))
        get = lambda k, d: fromMm(float(spec[k][0])) if spec[k] else fromMm(d)
        return get('rails', 9), get('sides', 5), get('space', 2)

    def buildFraming(self, panel):
        rails, sides, space = self._sizes()
        # makeFrame(widthH, widthV, ...): widthH = left / right rails, widthV = top / bottom
        panel.makeFrame(sides, rails, space, space)
        return []          # no cuts: the frame stays one piece

    def buildDummyFramingSubstrates(self, substrates):
        # thin stand-ins for the frame, so KiKit can build the partition line the tabs
        # extend to (same construction as KiKit's own frame dummies)
        rails, sides, space = self._sizes()
        minx = min(s.bounds()[0] for s in substrates); miny = min(s.bounds()[1] for s in substrates)
        maxx = max(s.bounds()[2] for s in substrates); maxy = max(s.bounds()[3] for s in substrates)
        w = fromMm(1)
        dummy = []
        for b in (box(minx, miny - 2 * space - w, maxx, miny - 2 * space),
                  box(minx, maxy + 2 * space, maxx, maxy + 2 * space + w),
                  box(minx - 2 * space - w, miny, minx - 2 * space, maxy),
                  box(maxx + 2 * space, miny, maxx + 2 * space + w, maxy)):
            sub = Substrate([]); sub.union(b); dummy.append(sub)
        return dummy
