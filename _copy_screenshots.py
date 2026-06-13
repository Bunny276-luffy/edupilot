import shutil
import os

src_dir = r'C:\Users\Yashasvi\.gemini\antigravity-ide\brain\6585599e-c105-45f6-9b69-939110deb3bc'
dst_dir = r'f:\projects\google\edupilot\_screenshots'

os.makedirs(dst_dir, exist_ok=True)

files = [
    ('home_1781023273598.png', 'home.png'),
    ('faculty_dashboard_1781023285701.png', 'faculty-dashboard.png'),
    ('student_chat_1781023298795.png', 'student-chat.png'),
]

for src_name, dst_name in files:
    src = os.path.join(src_dir, src_name)
    dst = os.path.join(dst_dir, dst_name)
    shutil.copy2(src, dst)
    print(f'Copied {dst_name}')

print('All screenshots copied successfully.')
