# KiKit tabs plugin: breakaway tabs at fixed x positions along the top and bottom
# edge of the board's bounding box, for rails on top and bottom (framing railstb).
# KiKit's own tab layouts space tabs along the bounding box, which on an outline
# like hachigo74's (angled halves, thumb keys hanging lower) gives long tabs into the
# middle of nowhere; here each tab sits where the outline actually reaches the rail.
#
# Preset (see <keyboard>/panel.json):
#   "tabs": {"type": "plugin", "code": "tools/lib/panel_tabs.py.FixedTabs",
#            "arg": "width 5; top 51.6 73.6; bottom 126.6 161.4", "fillet": "1mm"}
#   x values in mm from the left edge of the board's bounding box. A top tab starts
#   at the bbox top and runs down until it meets the outline, then up to the rail;
#   bottom tabs the other way round.
from kikit.plugin import TabsPlugin
from kikit.annotations import TabAnnotation
from kikit.common import fromMm


def parse(arg):
    spec = {'width': [5.0], 'top': [], 'bottom': []}
    for part in arg.split(';'):
        words = part.split()
        if not words: continue
        if words[0] not in spec: raise RuntimeError('panel_tabs: unknown key %r in %r' % (words[0], arg))
        spec[words[0]] = [float(w) for w in words[1:]]
    return spec['width'][0], spec['top'], spec['bottom']


class FixedTabs(TabsPlugin):
    def buildTabAnnotations(self, panel):
        width, top, bottom = parse(self.userArg)
        for s in panel.substrates:
            minx, miny, maxx, maxy = s.bounds()
            for x in top:
                s.annotations.append(TabAnnotation(None, (minx + fromMm(x), miny), (0, 1), fromMm(width)))
            for x in bottom:
                s.annotations.append(TabAnnotation(None, (minx + fromMm(x), maxy), (0, -1), fromMm(width)))
