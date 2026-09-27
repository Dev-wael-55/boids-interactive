import pygame
import math
import random
import sys

pygame.init()

WIDTH, HEIGHT = 1080, 1920
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME | pygame.DOUBLEBUF)
pygame.display.set_caption("Boids Interactive - Hold Space to Repel, Click to Attract")
clock = pygame.time.Clock()

NUM_BOIDS = 280
CIRCLE_RADIUS = 150.0

class Boid:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(3.0, 5.0)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.max_speed = 5.2
        self.max_force = 0.16
        self.size = 7.0

    def update(self):
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed
        elif speed < 2.0:
            self.vx = (self.vx / speed) * 2.0
            self.vy = (self.vy / speed) * 2.0

        self.x += self.vx
        self.y += self.vy

        # دوران الحواف اللانهائي
        if self.x < -20: self.x = WIDTH + 20
        elif self.x > WIDTH + 20: self.x = -20
        if self.y < -20: self.y = HEIGHT + 20
        elif self.y > HEIGHT + 20: self.y = -20

    def apply_forces(self, boids, target_pos, mode):
        # 1. القواعد الكلاسيكية للأسراب المنفصلة (Boids Rules)
        sep_dist = 26.0
        align_dist = 60.0
        coh_dist = 70.0

        sep_x, sep_y = 0.0, 0.0
        align_x, align_y = 0.0, 0.0
        coh_x, coh_y = 0.0, 0.0

        sep_cnt = 0
        align_cnt = 0
        coh_cnt = 0

        for other in boids:
            if other is self:
                continue

            dx = other.x - self.x
            dy = other.y - self.y
            d = math.hypot(dx, dy)

            # تفادي التصادم الموضعي
            if 0 < d < sep_dist:
                sep_x -= dx / d
                sep_y -= dy / d
                sep_cnt += 1

            # محاذاة السرعة مع المجموعة القريبة فقط لتشكيل أسراب صغيرة مستقلة
            if 0 < d < align_dist:
                align_x += other.vx
                align_y += other.vy
                align_cnt += 1

            # التماسك المحلي
            if 0 < d < coh_dist:
                coh_x += other.x
                coh_y += other.y
                coh_cnt += 1

        if sep_cnt > 0:
            sep_x /= sep_cnt
            sep_y /= sep_cnt
            self._steer(sep_x, sep_y, weight=1.8)

        if align_cnt > 0:
            align_x /= align_cnt
            align_y /= align_cnt
            self._steer(align_x - self.vx, align_y - self.vy, weight=1.1)

        if coh_cnt > 0:
            coh_x = (coh_x / coh_cnt) - self.x
            coh_y = (coh_y / coh_cnt) - self.y
            self._steer(coh_x, coh_y, weight=0.8)

        # 2. التفاعل مع الاختصارات وموضع الفأرة
        tx, ty = target_pos
        tdx = tx - self.x
        tdy = ty - self.y
        dist = math.hypot(tdx, tdy)

        if mode == "repel":
            # حالة الضغط على المسافة (SPACE): تشتيت وهروب طالما أنت ضاغط
            if dist < CIRCLE_RADIUS * 2.8:
                nx = -tdx / max(dist, 1.0)
                ny = -tdy / max(dist, 1.0)
                # دفع هروب قوي
                force = (1.0 - dist / (CIRCLE_RADIUS * 2.8)) * 14.0
                self.vx += nx * force
                self.vy += ny * force

        elif mode == "attract":
            # حالة الضغط على الزر (Click أو LSHIFT): جذب وتجمع ودوران داخل الدائرة
            if dist > 30.0:
                # قوة جذب للمركز
                self._steer(tdx / max(dist, 1.0), tdy / max(dist, 1.0), weight=1.6)
            else:
                # حركة دائرية انسيابية داخل المركز
                self.vx += -tdy * 0.08
                self.vy += tdx * 0.08

    def _steer(self, fx, fy, weight=1.0):
        mag = math.hypot(fx, fy)
        if mag > 0:
            fx = (fx / mag) * self.max_force * weight
            fy = (fy / mag) * self.max_force * weight
            self.vx += fx
            self.vy += fy

    def draw(self, surface):
        ang = math.atan2(self.vy, self.vx)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)

        # رسم سهم الطائر الدقيق والناعم
        tip_x = self.x + cos_a * (self.size * 1.6)
        tip_y = self.y + sin_a * (self.size * 1.6)

        left_x = self.x + math.cos(ang + 2.5) * self.size
        left_y = self.y + math.sin(ang + 2.5) * self.size

        right_x = self.x + math.cos(ang - 2.5) * self.size
        right_y = self.y + math.sin(ang - 2.5) * self.size

        notch_x = self.x - cos_a * (self.size * 0.4)
        notch_y = self.y - sin_a * (self.size * 0.4)

        points = [(tip_x, tip_y), (left_x, left_y), (notch_x, notch_y), (right_x, right_y)]
        pygame.draw.polygon(surface, (55, 235, 185), points)

# إنشاء الطيور متوزعة في أنحاء الشاشة
boids = [Boid(random.uniform(100, WIDTH - 100), random.uniform(200, HEIGHT - 200)) for _ in range(NUM_BOIDS)]

circle_x = float(WIDTH // 2)
circle_y = float(HEIGHT // 2)

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                boids = [Boid(random.uniform(100, WIDTH - 100), random.uniform(200, HEIGHT - 200)) for _ in range(NUM_BOIDS)]

    # تتبع موقع الماوس بانسيابية
    mx, my = pygame.mouse.get_pos()
    circle_x += (mx - circle_x) * 0.08
    circle_y += (my - circle_y) * 0.08
    target_pos = (circle_x, circle_y)

    # فحص الأزرار المضغوطة باستمرار (طالما اليد على الزر):
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()

    # 1. إذا ضغطت مسافة (SPACE): تشتيت وابتعاد
    if keys[pygame.K_SPACE]:
        current_mode = "repel"
    # 2. إذا ضغطت كليك يسار (أو زر SHIFT): جذب وتجمع ودوران في المكان
    elif mouse_buttons[0] or keys[pygame.K_LSHIFT] or keys[pygame.K_RETURN]:
        current_mode = "attract"
    # 3. الوضع الافتراضي: كل مجموعة تمشي لحالها بهدوء تام
    else:
        current_mode = "idle"

    # تحديث السرب
    for b in boids:
        b.apply_forces(boids, target_pos, current_mode)
        b.update()

    # الخلفية السوداء المائلة للكحلي العميق
    screen.fill((5, 9, 14))

    # رسم الدائرة التفاعلية الرقيقة بناءً على الحالة:
    if current_mode == "repel":
        # دائرة حمراء خافتة توضح منطقة النبذ والتشتيت
        pygame.draw.circle(screen, (220, 50, 70), (int(circle_x), int(circle_y)), int(CIRCLE_RADIUS), 1)
    elif current_mode == "attract":
        # دائرة سيان واضحة تلتف الطيور بداخلها
        pygame.draw.circle(screen, (55, 235, 185), (int(circle_x), int(circle_y)), int(CIRCLE_RADIUS), 1)
    else:
        # في الوضع الطبيعي تظهر دائرة خافتة جداً وغير مزعجة
        pygame.draw.circle(screen, (25, 65, 55), (int(circle_x), int(circle_y)), int(CIRCLE_RADIUS), 1)

    # رسم الطيور
    for b in boids:
        b.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()