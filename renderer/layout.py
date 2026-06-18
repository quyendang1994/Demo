class Layout:
    # Canvas
    canvas_w: int = 1080
    canvas_h: int = 1080

    # Spacing
    padding: int = 36
    header_h: int = 110
    footer_h: int = 52
    card_gap: int = 12
    num_cards: int = 5
    corner_r: int = 16

    # Colors (RGBA)
    bg_top: tuple = (13, 27, 42)        # deep navy
    bg_bottom: tuple = (22, 22, 58)     # dark indigo
    card_fill: tuple = (255, 255, 255, 22)
    card_outline: tuple = (255, 255, 255, 55)
    accent: tuple = (0, 168, 232)       # cyan
    accent_dark: tuple = (0, 120, 180)
    text_title: tuple = (255, 255, 255)
    text_body: tuple = (185, 200, 215)
    text_source: tuple = (0, 210, 255)
    text_header: tuple = (255, 255, 255)
    text_footer: tuple = (140, 160, 180)
    separator: tuple = (255, 255, 255, 40)

    # Font sizes
    size_header_brand: int = 30
    size_header_date: int = 18
    size_badge: int = 20
    size_title: int = 24
    size_body: int = 17
    size_source: int = 14
    size_footer: int = 14

    # Card thumbnail
    thumb_w: int = 112

    @property
    def card_area_top(self) -> int:
        return self.header_h + self.padding // 2

    @property
    def card_area_h(self) -> int:
        return self.canvas_h - self.header_h - self.footer_h - self.padding

    @property
    def card_h(self) -> int:
        return (self.card_area_h - self.card_gap * (self.num_cards - 1)) // self.num_cards

    @property
    def card_w(self) -> int:
        return self.canvas_w - self.padding * 2

    @property
    def card_x(self) -> int:
        return self.padding

    def card_y(self, index: int) -> int:
        return self.card_area_top + index * (self.card_h + self.card_gap)


layout = Layout()
