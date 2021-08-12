import random
import ssl

import requests, json, pymysql, uuid, re, crypt
import urllib3
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SpLeetCode:
    def __init__(self):
        self.problem_url = "https://leetcode.com/problems/{name}"
        self.header = {
            'Connection': 'close',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Content-Type': 'application/json',
            'Cookie': '_ga=GA1.2.852872472.1628149941; gr_user_id=3e007d11-24fa-49b5-9d7c-b71654b630f8; NEW_PROBLEMLIST_PAGE=1; _gid=GA1.2.864121436.1628661583; 87b5a3c3f1a55520_gr_session_id=48745ec8-4044-48b3-be60-4a5d74b7b873; 87b5a3c3f1a55520_gr_session_id_48745ec8-4044-48b3-be60-4a5d74b7b873=true; csrftoken=D3IVlHuOEmjZI2ipVOQWZ3KlKRsMeXo213ifTR85EojLamG1GDVOo4Wvewglkw68; messages="64b9c5c7602a50e54d5eef7638bcb6a4508a306c$[[\"__json_message\"\0540\05425\054\"Successfully signed in as BadAnswer.\"]]"; 87b5a3c3f1a55520_gr_last_sent_sid_with_cs1=48745ec8-4044-48b3-be60-4a5d74b7b873; 87b5a3c3f1a55520_gr_last_sent_cs1=BadAnswer; __stripe_mid=e4dbabd8-2ca6-488b-b700-d253273e0e123489e6; __stripe_sid=fc3fcddf-4e49-494d-a0e0-859509d09f91bfead9; LEETCODE_SESSION=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTg5NzEyOCIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiNGYxYmQwNmJkMzZkMjAzYmZjMjJiODllZWVlNjk3YzFiMDBmMTQ2YSIsImlkIjoxODk3MTI4LCJlbWFpbCI6ImNlYXNlcmJvcmdpYW5AZ21haWwuY29tIiwidXNlcm5hbWUiOiJCYWRBbnN3ZXIiLCJ1c2VyX3NsdWciOiJCYWRBbnN3ZXIiLCJhdmF0YXIiOiJodHRwczovL3d3dy5ncmF2YXRhci5jb20vYXZhdGFyL2E2NjMzYjY0NTQyZGNkZDdhM2U4NzFlY2ZiNTBlZjEwLnBuZz9zPTIwMCIsInJlZnJlc2hlZF9hdCI6MTYyODY2NjU4OCwiaXAiOiIxMzcuMTE2LjE3My4zIiwiaWRlbnRpdHkiOiJiZTM0MTlhOGI1NzU3YWEzMzRkMDg3Y2YzMTdjMjQ1NiIsInNlc3Npb25faWQiOjExNDY3NTEzLCJfc2Vzc2lvbl9leHBpcnkiOjEyMDk2MDB9.TH80mDVW_YDonCBzdEYol-HcaD0fFG35Cn7ZY1BzqAA; _gat=1; 87b5a3c3f1a55520_gr_cs1=BadAnswer; c_a_u=QmFkQW5zd2Vy:1mDilN:FhWQ-HKP9YaTTLpM3FfIfsJneYw'
        }

    def get_response(self, url):
        response = requests.get(url).content
        return response.decode("utf-8")

    def sp_all_problem(self):
        url = "https://leetcode.com/api/problems/all/"
        json_date = json.loads(self.get_response(url))
        problem_list = json_date['stat_status_pairs']

        db = pymysql.connect(host="localhost", port=3306, user="root", password="11111111", db="leetcode_db",
                             connect_timeout=2000)
        cursor = db.cursor()

        result = []

        for problem in problem_list:
            id = problem['stat']['question_id']
            problem_name = problem['stat']['question__title_slug']
            print("正在获取第%s题： %s" % (id, problem_name))
            # 跳过付费题目
            if problem['paid_only']:
                print("题目付费，已跳过")
                continue
            problem_detail = self.get_problem_by_name(problem_name)
            problem_difficulty = problem_detail['difficulty']
            # 清洗content中的html标签
            problem_content = self.clear_problem_content(problem_detail['content'])
            print("content: "+problem_content)
            problem_json = {
                'title': problem_name,
                'difficulty': problem_difficulty,
                'content': problem_content
            }
            result.append(problem_json)
            # 写入数据库
            sql = "insert into `problem`(`title`,`difficulty`,`content`,`uuid`) values ('%s','%s','%s','%s')" % \
                  (problem_name, problem_difficulty, problem_content, uuid.uuid4())
            try:
                print("写入数据库")
                db.ping(reconnect=True)
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                print("写入失败,msg: ", e)
                db.rollback()
            db.close()

        with open("./problem.json", "w+") as f:
            json.dump(result, f)



    # 清洗html标签
    def clear_problem_content(self, content):
        reg = re.compile('<[^>]*>')
        result = reg.sub('', content)
        return result

    def get_problem_by_name(self, slug):
        url = "https://leetcode.com/graphql"
        params = {'operationName': "getQuestionDetail",
                  'variables': {'titleSlug': slug},
                  'query': '''query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    questionFrontendId
                    questionTitle
                    questionTitleSlug
                    content
                    difficulty
                    stats
                    similarQuestions
                    categoryTitle
                    topicTags {
                            name
                            slug
                    }
                }
            }'''
                  }
        json_data = json.dumps(params).encode('utf8')
        headers = {
            'Connection': 'close',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com/problems/' + slug,
            'Cookie': '_ga=GA1.2.852872472.1628149941; gr_user_id=3e007d11-24fa-49b5-9d7c-b71654b630f8; NEW_PROBLEMLIST_PAGE=1; _gid=GA1.2.864121436.1628661583; 87b5a3c3f1a55520_gr_session_id=48745ec8-4044-48b3-be60-4a5d74b7b873; 87b5a3c3f1a55520_gr_session_id_48745ec8-4044-48b3-be60-4a5d74b7b873=true; csrftoken=D3IVlHuOEmjZI2ipVOQWZ3KlKRsMeXo213ifTR85EojLamG1GDVOo4Wvewglkw68; messages="64b9c5c7602a50e54d5eef7638bcb6a4508a306c$[[\"__json_message\"\0540\05425\054\"Successfully signed in as BadAnswer.\"]]"; 87b5a3c3f1a55520_gr_last_sent_sid_with_cs1=48745ec8-4044-48b3-be60-4a5d74b7b873; 87b5a3c3f1a55520_gr_last_sent_cs1=BadAnswer; __stripe_mid=e4dbabd8-2ca6-488b-b700-d253273e0e123489e6; __stripe_sid=fc3fcddf-4e49-494d-a0e0-859509d09f91bfead9; LEETCODE_SESSION=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJfYXV0aF91c2VyX2lkIjoiMTg5NzEyOCIsIl9hdXRoX3VzZXJfYmFja2VuZCI6ImRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kIiwiX2F1dGhfdXNlcl9oYXNoIjoiNGYxYmQwNmJkMzZkMjAzYmZjMjJiODllZWVlNjk3YzFiMDBmMTQ2YSIsImlkIjoxODk3MTI4LCJlbWFpbCI6ImNlYXNlcmJvcmdpYW5AZ21haWwuY29tIiwidXNlcm5hbWUiOiJCYWRBbnN3ZXIiLCJ1c2VyX3NsdWciOiJCYWRBbnN3ZXIiLCJhdmF0YXIiOiJodHRwczovL3d3dy5ncmF2YXRhci5jb20vYXZhdGFyL2E2NjMzYjY0NTQyZGNkZDdhM2U4NzFlY2ZiNTBlZjEwLnBuZz9zPTIwMCIsInJlZnJlc2hlZF9hdCI6MTYyODY2NjU4OCwiaXAiOiIxMzcuMTE2LjE3My4zIiwiaWRlbnRpdHkiOiJiZTM0MTlhOGI1NzU3YWEzMzRkMDg3Y2YzMTdjMjQ1NiIsInNlc3Npb25faWQiOjExNDY3NTEzLCJfc2Vzc2lvbl9leHBpcnkiOjEyMDk2MDB9.TH80mDVW_YDonCBzdEYol-HcaD0fFG35Cn7ZY1BzqAA; _gat=1; 87b5a3c3f1a55520_gr_cs1=BadAnswer; c_a_u=QmFkQW5zd2Vy:1mDilN:FhWQ-HKP9YaTTLpM3FfIfsJneYw'
        }
        # s = requests.Session()
        # s.mount('https://', MyAdapter())
        resp = requests.post(url, data=json_data, headers=headers, timeout=2000, verify=False)
        content = resp.json()
        # 题目详细信息
        question = content['data']['question']
        return question


t = SpLeetCode()
t.sp_all_problem()
