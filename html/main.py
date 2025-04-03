from flask import Flask, render_template, request, session
import random
from collections import deque

# إنشاء تطبيق Flask
app = Flask(__name__)
# تعيين مفتاح سري للجلسة (يجب تغييره لقيمة آمنة في الإنتاج)
app.secret_key = '123'


def generate_maze(rows, cols, obstacle_prob=0.2):
    """
    دالة توليد متاهة عشوائية.

    - rows: عدد الصفوف في المتاهة.
    - cols: عدد الأعمدة في المتاهة.
    - obstacle_prob: احتمال أن تكون الخلية عقبة (1).

    تُنشئ الدالة مصفوفة (قائمة من القوائم) بحجم (rows x cols)
    بحيث تكون قيمة كل خلية 1 (عقبة) إذا كان الرقم العشوائي أقل من obstacle_prob، وإلا تكون 0 (طريق).
    كما يتم التأكد من أن نقطة البداية (0,0) ونقطة الهدف (rows-1, cols-1) مفتوحتان (0).
    """
    maze = [[1 if random.random() < obstacle_prob else 0 for _ in range(cols)] for _ in range(rows)]
    maze[0][0] = 0  # تأكيد أن نقطة البداية مفتوحة
    maze[rows - 1][cols - 1] = 0  # تأكيد أن نقطة الهدف مفتوحة
    return maze


def bfs(maze, start, goal):
    """
    دالة حل المتاهة باستخدام خوارزمية البحث بالعرض (BFS).

    - maze: مصفوفة المتاهة.
    - start: نقطة البداية على شكل (row, col).
    - goal: نقطة الهدف على شكل (row, col).

    تقوم الخوارزمية بالبحث عن المسار الأقصر (من حيث عدد الخلايا) من البداية إلى الهدف.
    تُعيد الدالة قائمة من الإحداثيات تمثل المسار، أو تُعيد None إذا لم يوجد مسار.
    """
    rows = len(maze)
    cols = len(maze[0])
    # إنشاء مصفوفة visited لتتبع الخلايا التي تمت زيارتها، وتكون جميع قيمها False في البداية
    visited = [[False] * cols for _ in range(rows)]
    # قاموس لتخزين "الوالد" (الخلية السابقة لكل خلية) لإعادة بناء المسار لاحقًا
    parent = {}
    # إنشاء قائمة انتظار (queue) وإضافة نقطة البداية إليها
    queue = deque([start])
    visited[start[0]][start[1]] = True

    # تحديد الاتجاهات الأربعة للتحرك: يمين، أسفل، يسار، أعلى
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    while queue:
        current = queue.popleft()
        # إذا تم الوصول للهدف، نخرج من الحلقة
        if current == goal:
            break
        r, c = current
        # استكشاف الخلايا المجاورة في جميع الاتجاهات
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # التأكد من أن الخلية الجديدة ضمن حدود المتاهة
            if 0 <= nr < rows and 0 <= nc < cols:
                # إذا كانت الخلية مفتوحة (0) ولم تتم زيارتها بعد
                if maze[nr][nc] == 0 and not visited[nr][nc]:
                    visited[nr][nc] = True  # وسم الخلية بأنها تمت زيارتها
                    parent[(nr, nc)] = current  # تسجيل الخلية الحالية كوالد للخلية الجديدة
                    queue.append((nr, nc))

    # إعادة بناء المسار من الهدف إلى البداية باستخدام parent
    path = []
    # إذا لم يتم الوصول للهدف (أي لم يتم تسجيل الهدف في parent) نعيد None
    if goal not in parent and start != goal:
        return None
    node = goal
    path.append(node)
    # تتبع الوالد حتى نصل إلى نقطة البداية
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()  # عكس المسار ليصبح من نقطة البداية إلى الهدف
    return path


def dfs(maze, start, goal):
    """
    دالة حل المتاهة باستخدام خوارزمية البحث بالتعمّق (DFS).

    - maze: مصفوفة المتاهة.
    - start: نقطة البداية على شكل (row, col).
    - goal: نقطة الهدف على شكل (row, col).

    تقوم الخوارزمية بالبحث عن مسار من نقطة البداية إلى الهدف باستخدام مكدس (stack).
    ملاحظة: DFS لا يضمن إيجاد أقصر مسار.
    تُعيد الدالة قائمة من الإحداثيات تمثل المسار، أو تُعيد None إذا لم يوجد مسار.
    """
    rows = len(maze)
    cols = len(maze[0])
    # مصفوفة visited لتتبع الخلايا التي تمت زيارتها
    visited = [[False] * cols for _ in range(rows)]
    parent = {}
    # استخدام مكدس (stack) لتخزين الخلايا التي سيتم زيارتها
    stack = [start]

    while stack:
        current = stack.pop()
        r, c = current
        # إذا كانت الخلية قد زُيِّرت مسبقًا، نتخطاها
        if visited[r][c]:
            continue
        visited[r][c] = True  # وسم الخلية بأنها تمت زيارتها
        # إذا وصلنا إلى الهدف، نخرج من الحلقة
        if current == goal:
            break
        # استكشاف الخلايا المجاورة في الاتجاهات الأربعة
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = r + dr, c + dc
            # التاكد من حدود المتاهة
            if 0 <= nr < rows and 0 <= nc < cols:
                # التاكد من الزيارة وهل تم زيارته
                if maze[nr][nc] == 0 and not visited[nr][nc]:
                    stack.append((nr, nc))
                    # حفظ الخلية الحالية كوالد للخلية الجديدة إن لم تكن محفوظة سابقًا
                    if (nr, nc) not in parent:
                        parent[(nr, nc)] = current

    # إعادة بناء المسار باستخدام parent
    path = []
    if goal not in parent and start != goal:
        return None
    node = goal
    path.append(node)
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


@app.route('/', methods=["GET"])
def index():
    """
    الراوت الرئيسي لعرض صفحة حل المتاهة.

    - يتم قراءة معلمات URL لتحديد:
      * حجم المتاهة (size)
      * الخوارزمية المختارة (algorithm)
      * هل يتم حل المتاهة أم توليد متاهة جديدة (solved)
    - تُستخدم الجلسة (session) لتخزين المتاهة حتى لا تتغير عند الضغط على زر "حل المتاهة".
    """
    # قراءة زر الخوارزمية من الرابط (افتراضي BFS)
    algorithm = request.args.get('algorithm', 'bfs').lower()
    try:
        # قراءة حجم المتاهة وتحويله إلى عدد صحيح (افتراضي 10)
        size = int(request.args.get('size', 10))
    except ValueError:
        size = 10
    # قراءة زر solved وتحويلها إلى قيمة منطقية (True إذا كانت "true")
    solved = request.args.get('solved', 'false').lower() == 'true'

    # استرجاع المتاهة من الجلسة إذا كانت موجودة
    maze = session.get('maze')
    # إذا لم توجد متاهة أو كان حجمها مختلف أو إذا كان المطلوب توليد متاهة جديدة (solved=False)
    if maze is None or len(maze) != size or len(maze[0]) != size or not solved:
        maze = generate_maze(size, size, obstacle_prob=0.2)
        session['maze'] = maze  # تخزين المتاهة في الجلسة

    start_point = (0, 0)  # نقطة البداية ثابتة في الزاوية العلوية اليسرى
    goal_point = (size - 1, size - 1)  # نقطة الهدف في الزاوية السفلية اليمنى
    path = None

    # إذا تم الضغط على زر "حل المتاهة" يتم استخدام المتاهة المخزنة دون تغييرها
    if solved:
        if algorithm == 'bfs':
            path = bfs(maze, start_point, goal_point)
        elif algorithm == 'dfs':
            path = dfs(maze, start_point, goal_point)

    # عرض الصفحة مع تمرير المتغيرات المطلوبة للقالب
    return render_template('index.html',
                           maze=maze,
                           path=path,
                           start=start_point,
                           goal=goal_point,
                           algorithm=algorithm,
                           size=size)


if __name__ == '__main__':
    # تشغيل التطبيق مع تفعيل وضع التصحيح (debug)
    app.run(debug=True)
