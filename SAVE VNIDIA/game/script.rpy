define News = Character("News Reporter", color="#cccccc")
define Ivan = Character("Ivan", color="#890000")
define Till = Character("Till", color="#2c9196")
define Mizi = Character("Mizi", color="#ff77aa")
define Sua = Character("Sua", color="#6655cc")
define Alien = Character("Alien", color="#a074a0")

define red_flash = Fade(0.2, 0.3, 0.4, color="#aa0000")

default round1_won = False
default round2_won = False


init python:
    import random
    import pygame_sdl2 as pygame

    def _hit(ax, ay, aw, ah, bx, by, bw, bh):
        """Simple axis-aligned rectangle overlap test."""
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    class StockWaveGame(renpy.Displayable):
        def __init__(self, target_obstacles=8, scroll_speed=480.0, **kwargs):
            super(StockWaveGame, self).__init__(**kwargs)
            self.width = 1920
            self.height = 1080

            # Player block
            self.block_x = 380.0
            self.block_y = 540.0
            self.block_size = 28
            self.vy = 0.0

            # Physics tuning
            self.gravity = 1450.0
            self.lift = -2900.0
            self.max_speed = 700.0
            self.scroll_speed = scroll_speed

            # Obstacles & finish line
            self.target_obstacles = target_obstacles
            self.obstacle_width = 110
            self.gap_height = 310
            self.obstacle_spacing = 680
            self.obstacles = []
            self.finish_x = 0.0

            # Trail & timing
            self.trail = []
            self.last_st = None
            self.game_over = False
            self.result = None
            self.end_st = None

            # Optional custom images (fall back to drawn shapes if missing)
            self.bg_img = renpy.displayable("chart_bg.png") if renpy.loadable("chart_bg.png") else None
            self.player_img = renpy.displayable("player_block.png") if renpy.loadable("player_block.png") else None
            self.top_obs_img = renpy.displayable("pillar_top.png") if renpy.loadable("pillar_top.png") else None
            self.bot_obs_img = renpy.displayable("pillar_bottom.png") if renpy.loadable("pillar_bottom.png") else None

            self._spawn_course()

        def _spawn_course(self):
            start_x = 1400.0
            for i in range(self.target_obstacles):
                ox = start_x + (i * self.obstacle_spacing)
                gap_y = random.randint(180, self.height - 180 - self.gap_height)
                self.obstacles.append({
                    "x": ox,
                    "gap_y": gap_y,
                    "color": random.choice(["#ff3b3b", "#00ff88"]),
                })
            self.finish_x = start_x + (self.target_obstacles * self.obstacle_spacing) + 200

        def _end(self, result, st):
            if not self.game_over:
                self.game_over = True
                self.result = result
                self.end_st = st
                renpy.timeout(0.3)

        def render(self, width, height, st, at):
            if self.last_st is None:
                dt = 0.016
            else:
                dt = min(st - self.last_st, 0.05)
            self.last_st = st

            if not self.game_over:
                keys = pygame.key.get_pressed()
                mouse_held = pygame.mouse.get_pressed()[0]
                thrust_held = keys[pygame.K_SPACE] or mouse_held

                prev_y = self.block_y

                if thrust_held:
                    self.vy += self.lift * dt
                else:
                    self.vy += self.gravity * dt

                self.vy = max(-self.max_speed, min(self.max_speed, self.vy))
                self.block_y += self.vy * dt

                # Floor / ceiling crash
                if self.block_y <= 0 or self.block_y + self.block_size >= self.height:
                    self.block_y = max(0, min(self.height - self.block_size, self.block_y))
                    self._end("lose", st)

                # Trail
                color = "#00ff88" if self.block_y < prev_y else "#ff3b3b"
                cx = self.block_x + self.block_size / 2.0
                cy = self.block_y + self.block_size / 2.0
                self.trail.append([cx, cy, color])

                new_trail = []
                for pt in self.trail:
                    pt[0] -= self.scroll_speed * dt
                    if pt[0] > -30:
                        new_trail.append(pt)
                self.trail = new_trail

                px = self.block_x + 4
                py = self.block_y + 4
                ps = self.block_size - 8

                # Obstacles
                for obs in self.obstacles:
                    obs["x"] -= self.scroll_speed * dt
                    ox = obs["x"]
                    gap_y = obs["gap_y"]
                    bot_y = gap_y + self.gap_height

                    if _hit(px, py, ps, ps, ox, 0, self.obstacle_width, gap_y) or \
                        _hit(px, py, ps, ps, ox, bot_y, self.obstacle_width, self.height - bot_y):
                        self._end("lose", st)

                # Finish line
                self.finish_x -= self.scroll_speed * dt
                if self.block_x >= self.finish_x:
                    self._end("win", st)

            r = renpy.Render(self.width, self.height)

            # 1. Background
            if self.bg_img:
                r.blit(renpy.render(self.bg_img, self.width, self.height, st, at), (0, 0))
            else:
                canvas = r.canvas()
                canvas.rect("#0f1216", (0, 0, self.width, self.height))
                for gx in range(0, self.width, 160):
                    canvas.line("#1c222b", (gx, 0), (gx, self.height), 2)
                for gy in range(0, self.height, 135):
                    canvas.line("#1c222b", (0, gy), (self.width, gy), 2)

            # 2. Obstacles
            use_obs_imgs = self.top_obs_img is not None and self.bot_obs_img is not None
            canvas = r.canvas()
            for obs in self.obstacles:
                ox = int(obs["x"])
                top_h = int(obs["gap_y"])
                bot_y = int(obs["gap_y"] + self.gap_height)
                bot_h = int(self.height - bot_y)

                if use_obs_imgs:
                    r.blit(renpy.render(self.top_obs_img, self.obstacle_width, top_h, st, at), (ox, 0))
                    r.blit(renpy.render(self.bot_obs_img, self.obstacle_width, bot_h, st, at), (ox, bot_y))
                else:
                    canvas.rect(obs["color"], (ox, 0, self.obstacle_width, top_h))
                    canvas.rect("#ffffff", (ox + 6, 0, self.obstacle_width - 12, top_h), 2)
                    canvas.rect(obs["color"], (ox, bot_y, self.obstacle_width, bot_h))
                    canvas.rect("#ffffff", (ox + 6, bot_y, self.obstacle_width - 12, bot_h), 2)

            # 3. Finish line
            canvas = r.canvas()
            fx = int(self.finish_x)
            if fx < self.width + 100:
                canvas.rect("#ffd700", (fx, 0, 16, self.height))
                for fy in range(0, self.height, 40):
                    canvas.rect("#111111", (fx, fy, 8, 20))
                    canvas.rect("#111111", (fx + 8, fy + 20, 8, 20))

            for i in range(1, len(self.trail)):
                p1 = self.trail[i - 1]
                p2 = self.trail[i]
                canvas.line(p2[2], (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 6)

            # 5. Player
            bx = int(self.block_x)
            by = int(self.block_y)
            if self.player_img:
                r.blit(renpy.render(self.player_img, self.block_size, self.block_size, st, at), (bx, by))
            else:
                canvas.rect("#ffffff", (bx, by, self.block_size, self.block_size))

            if not self.game_over:
                renpy.redraw(self, 0)
            return r

        def event(self, ev, x, y, st):
            # Wait a moment after crash/win so the player sees what happened
            if self.game_over and self.end_st is not None and (st - self.end_st) >= 0.25:
                return self.result
            return None



screen stock_minigame(obstacles=8, speed=480.0):
    default game = StockWaveGame(target_obstacles=obstacles, scroll_speed=speed)
    add game
    text "HOLD [[SPACE]] OR CLICK TO DRIVE STOCK UP" xpos 40 ypos 30 size 28 color "#aaaaaa"


screen click_ivan_nametag():
    modal True
    frame:
        xalign 0.5
        yalign 0.45
        padding (40, 20)
        background "#890000"
        textbutton "IVAN":
            text_size 48
            text_color "#ffffff"
            text_hover_color "#ffd700"
            action Return()


screen big_start_button():
    modal True
    add Solid("#0f1216")
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 30
        text "NVIDIA MARKET STABILIZER v1.0" xalign 0.5 size 42 color "#00ff88"
        textbutton "START TRADING":
            xalign 0.5
            padding (80, 40)
            background "#00aa55"
            hover_background "#00ff88"
            text_size 64
            text_color "#ffffff"
            text_hover_color "#000000"
            action Return()



label start:

    scene newsreportbg with fade
    News "BREAKING NEWS!"
    News "NVIDIA stocks are plummeting rapidly AGAIN after Jensen's latest affair!"
    News "Analysts are in a panic as the chart goes straight into the red."

    Ivan "Well, this is convenient..."

    "*DING!*" 


    scene phonebg with fade
    Till "They just assigned us a new task..."
    Mizi "There's just more and more work..."
    Sua "Don't mess this up. Management is watching the live ticker."

    scene cubiclebg with fade
    "*ZAP!* An Alien suddenly teleports into your cubicle."
    Alien "HUMAN. YOU HAVE BEEN SELECTED TO MANUALLY STABILIZE THE STOCK CHART."
    Alien "KEEP THE LINE IN THE GREEN. DO NOT HIT THE MARKET CANDLES."

    call screen big_start_button
    call screen stock_minigame(obstacles=7, speed=480.0)
    $ round1_won = (_return == "win")

    with red_flash

    if round1_won:
        Till "Whoa, you actually pulled the stock back up! Nice work!"
        Mizi "Keep going! One more push and the market closes in the green!"
        Sua "Not bad. Stay focused for the final stretch."
    else:
        Sua "...That was a massive dip. What are you doing?"
        Mizi "It's okay, there's still time before the closing bell! You got this!"
        Till "Yeah, don't give up now. Just steady the line!"

    call screen big_start_button
    call screen stock_minigame(obstacles=9, speed=560.0)
    $ round2_won = (_return == "win")

    with red_flash

    if round1_won and round2_won:
        jump ending_good
    elif (not round1_won) and (not round2_won):
        jump ending_bad
    else:
        jump ending_secret


label ending_good:
    scene newsreportbg with fade
    News "UNBELIEVABLE! NVIDIA stocks have skyrocketed to an all-time high!"
    Ivan "Looks like we have a new CEO."
    Till "Hey... congrats on the promotion. Want to celebrate after work?"
    "ENDING 1: GOOD ENDING — CEO & Till's Affection"
    return


label ending_bad:
    scene newsreportbg with fade
    News "TOTAL COLLAPSE. NVIDIA shares have hit zero."
    Alien "YOU HAVE FAILED THE QUOTA. TERMINATING EMPLOYEE."
    "*PEW!*"
    "ENDING 2: BAD ENDING — Fired (Literally)"
    return


label ending_secret:
    scene newsreportbg with fade
    News "Markets close completely flat today after a wild rollercoaster session."
    Ivan "Well, you didn't save the company, so no promotion. At least you aren't fired."
    "*DING!*"
    Till "Hey, rough day on the charts. Wanna grab coffee and forget about work?"
    "You meet up with Till at a quiet café away from the office..."
    "ENDING 3: SECRET ENDING — Coffee Date with Till"
    return
