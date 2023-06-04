from typing import Dict
import requests
import base64
import termcolor
import pathlib
import wget
import PIL
import multiprocessing
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

hfs_session_id = ''
waiting_download_pictures = []  # [{'name': 'picture_url'}]

def login(username: str, password: str):
    req = requests.post(
        'https://hfs-be.yunxiao.com/v2/users/sessions',
        {
            'loginName': username,
            'password': base64.b64encode(password.encode('utf-8')).decode('utf-8'),
            'loginType': 1,
            'rememberMe': 2,
            'roleType': 1
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi K30 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
            'Referer': 'http://www.haofenshu.com/',
            'Origin': 'http://www.haofenshu.com'
        }
    )
    
    return req.cookies.get('hfs-session-id')

def get_exam_list():
    req = requests.get(
        'https://hfs-be.yunxiao.com/v3/exam/list?start=0&limit=10',
        headers={
            'hfs-token': hfs_session_id
        }
    )
    
    return req.json()['data']['list']

def get_subject_list(exam_id: str):
    req = requests.get(
        f'https://hfs-be.yunxiao.com/v3/exam/{exam_id}/overview',
        headers={
            'hfs-token': hfs_session_id
        }
    )
    
    return req.json()['data']['papers']

def get_wrong_question(exam_id: str, paper_id: str, exam_name: str, paper_name: str):
    req = requests.get(
        f'https://hfs-be.yunxiao.com/v3/exam/{exam_id}/papers/{paper_id}/question-detail',
        headers={
            'hfs-token': hfs_session_id
        }
    )
    
    questions = req.json()['data']['questionList']
    wrong_questions = []
    
    for question in questions:
        if question['isWrong'] != 2:
            wrong_questions.append(question)
            print(
                f'{exam_name} 的 {paper_name} 试卷上的',
                termcolor.colored(
                    f'{question["name"]} 为错题',
                    'red'
                )
            )
            
            waiting_download_pictures.append({
                'name': f"{question['name']}_{paper_name}_{exam_name}",
                'url': question['pictures'][0],
                'my_answer': question['myAnswer'],
                'answer': question['answer']
            })
        else:
            print(
                f'{exam_name} 的 {paper_name} 试卷上的',
                termcolor.colored(
                    f'{question["name"]} 为正确题',
                    'green'
                )
            )
    
    return wrong_questions

def image_add_text(img_path, text, left, top, text_color=(255, 0, 0), text_size=13):
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype("XiaolaiSC-Regular.ttf", text_size, encoding="utf-8")
    # 绘制文本
    draw.text((left, top), text, text_color, font=fontStyle)
    return img

def download_pictures(picture: Dict[str, str]):
    name = picture['name']
    print(termcolor.colored(f'正在下载 {name}'))
    url = picture['url']
    
    req = requests.get(url)
    content = req.content
    
    im = image_add_text(
        BytesIO(content),
        f'你的作答：{picture["my_answer"]}\n正确答案：{picture["answer"]}',
        0,
        0,
        text_color=(24, 131, 183),
        text_size=45
    )
    
    im.save(f'./pictures/{name}.png')
    
if '__main__' == __name__:
    if pathlib.Path('./pictures').exists() is False:
        pathlib.Path('./pictures').mkdir()
    
    print(
        termcolor.colored('本程序由：', 'green'), termcolor.colored('XYCode | 何雨壕', 'blue'), termcolor.colored('开发，搬运需要注明作者', 'green')
    )
    
    
    username = input('请输入手机号：')
    password = input('请输入密码：')
    # username = '13187949038'
    # password = '20100308hyh'
    
    hfs_session_id = login(username, password)
    print(
        termcolor.colored(
            '已完成登录',
            'blue'
        )
    )
    
    exam_list = get_exam_list()
    exam_list_str = []
    
    for exam, index in zip(exam_list, range(len(exam_list))):
        exam_list_str.append(
            termcolor.colored(f'{index}. ', 'blue') + termcolor.colored(exam['name'], 'green')
        )
    
    print('\n'.join(exam_list_str))
    
    select = int(input('请输入考试序号：'))
    # select = 0
    exam = exam_list[select]
    subjects = get_subject_list(exam['examId'])
    
    print(termcolor.colored('开始爬取试题', 'blue'))
    for subject in subjects:
        print(f'正在爬取 {subject["name"]} 试卷上的错题')
        get_wrong_question(exam['examId'], subject['paperId'], exam['name'], subject['name'])
    
    print(
        termcolor.colored(
            '试题爬取成功',
            'blue'
        ),
        '\n',
        termcolor.colored(
            '开始下载图片',
            'blue'
        )
    )
    
    
    for picture in waiting_download_pictures:
        download_pictures(picture)
        # pool.apply_async(download_pictures, (picture,))
    
    input(
        termcolor.colored(
            '下载完成，按下任意键退出',
            'red'
        )
    )
    