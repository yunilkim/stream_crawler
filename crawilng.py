# 라이브러리 임포트
import requests # 인터넷 주소(url) 에 html 파일을 요청
from bs4 import BeautifulSoup # 그렇게 해서 얻어온 html 파일을 예쁘게 '파싱'(필요정보추출)
import pandas as pd
import re   # 정규표현식(re), 문자열 정제
import time
from io import StringIO

# buffer(임시 데이터) 상태인 df를 encode한 후
# 결과를 반환해주는 콛
# 지금은 내 컴퓨터(로컬)이지만, 배포 후 '클라우드'에 존재
# 클라우드에서 임시파일인 buffer를
# 나의 컴퓨터로 다운로드 상태로 만듬
def download_to_csv(df):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode('utf-8-sig')

# 검색어, 제외할검색어, 지역, 직무, 경력, 학력, 페이지 수
# 매개변수에 입력될 자료형 '미리 안내'

# url, header, parameters => requests.get(주소) 주소로 요청
# soup 객체로 파싱, 가지고 있다가 select()
def crawling_saramin(search_text:str, except_text:str = '', region:list = None, category:list = None, career:str = '', education:str = '', max_pages:int = 1) -> pd.DataFrame:
    # 결과로 반환할 데이터 프레임의 '열 이름'과 '행' 리스트
    columns = ['이름', '위치', '조건1', '조건2', '회사이름', '링크']
    rows = []
    
    # requests 로 '검색할 페이지'에 요청 
    url = "https://www.saramin.co.kr/zf_user/search"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"
    }
    for page in range(1, max_pages +1):
        # 파라미터 정제
        # '키' 웹 사이트 지정한 '키'
        # print(f'page: {page}')
        parameters = {'searchword':search_text,
                        'except_read':except_text,
                        'recruitPage':page,
                        # 'comp_page':page,
                    }
        # 직무
        if category:
            parameters['cat_mcd'] = category
        # 위치
        if region:
            parameters['loc_mcd'] = region
        # 경력
        if career:
            parameters['career_cd'] = career
        # 학력
        if education:
            parameters['edu_cd'] = education

        try:
            res = requests.get(url=url, headers=headers, 
                                params=parameters, # 조건에 대한 정보
                                timeout=15) # html 반환해줄때까지 대기시간

            # 크롤링 결과를 response로 받고
            # response 안에 있는 text 파일을 'html.parser'로 파싱
            # 객체 soup를 생성
            soup = BeautifulSoup(res.text, 'html.parser')

            # 내가 필요한 결과의 'id'전달, 추출
            # soup.select(id) : id 를 보유한 모든 내용
            # soup.select_one(id) : id를 보유한 내용 딱 하나
            items = soup.select('div.item_recruit')
            for item in items:
                job_area = item.select_one('div.area_job')
                corp_area = item.select_one('div.area_corp')
                
                if not job_area:
                    continue
                
                # 직무, 회사정보 get
                job_title = job_area.select_one('.job_tit').get_text(strip=True)
                condition_area = job_area.select_one('div.job_condition')
                spans = condition_area.select('span')

                location = spans[0].get_text(strip=True)
                condition1 = spans[1].get_text(strip=True)

                # condition2 = spans[-1].get_text(strip=True)
                job_sector = item.select_one('div.job_sector')
                condition2 = job_sector.get_text(strip=True)

                # 회사정보
                corp_name = corp_area.select_one('.corp_name').get_text(strip=True)

                # 링크
                link = job_area.select_one('.job_tit').select_one('.data_layer[href]')
                real_link = 'https://www.saramin.co.kr' + link.get('href')
                # print(type(job_title), type(location),type(condition1),type(job_sector),type(corp_name)) 
                rows.append({
                    '이름': job_title,
                    '위치': location,
                    '조건1': condition1,
                    '조건2': condition2,
                    '회사이름': corp_name,
                    '링크': real_link
                })
        except Exception as e:
            print(f'Error saramin : {e}')
        time.sleep(1)
    df = pd.DataFrame(rows)
    return df

def crawling_work24(search_text:str, except_text:str = '', region:list = None, category:list = None, career:str = '', education:str = '', max_pages:int = 1):
    url = 'https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do'
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        }

    rows = []
    for page in range(1, max_pages + 1):
        # print(f'page: {page}')
        # 1. request
        parameters = {'srcKeyword': search_text,
                        'notSrcKeyword': except_text,
                        'pageIndex': page,
                        'resultCnt': 10,
                        'CodeDepth1Info': region,
                        'occupation': '024',
                        'careerTypes': '',
                        'academicGbnoEdu': ''
                    }
    
        try:
            response = requests.get(url, headers=headers, params=parameters, timeout=15)
            # print(response.status_code)
            # 2. soup 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items_1 = soup.select('div.box_table_group.gap_box08.column')
            items_2 = soup.select('td.link.pd24')
            for item_1, item_2 in zip(items_1, items_2):
                job_title = item_1.select_one('.t3_sb.underline_hover').get_text(strip=True)
                location = item_2.select_one('li.site').get_text(strip=True)
                career_spans = item_2.select('span.item.sm')
                condition1 = career_spans[0].get_text(strip=True) + ', ' + career_spans[1].get_text(strip=True)
                condition1 = condition1.replace('\n','').replace('\t','').replace('\r','')
                # salary
                salary = item_2.select_one('span.item.b1_sb').get_text(strip=True)
                salary = salary.replace('\n','').replace('\t','').replace('\r','')
                # 정규표현식으로 처리
                # import re
                # salary = re.sub(r'\s+', '', salary)

                # corp_name 
                # cells = item_1.select('div.cell')   
                # name = cells[1].get_text(strip=True)
                # corp_name = cells[0].get_text(strip=True) 
                corp_name = item_1.select_one('.cp_name.underline_hover').get_text(strip=True)

                if item_2.select_one('ul.emp_info_dtl').has_attr('li'):
                    t = ''
                    work_time = item_2.select_one('ul.emp_info_dtl').select_one('li.time')
                    if len(work_time) > 1:
                            for i in range(len(work_time)):
                                t += work_time.select('span')[i].text
                    elif len(work_time) == 1:
                        t = work_time.select_one('span').text
                    else:
                        t = ''
                    work_time = t
                else:
                    work_time = "모름"

                work_time = re.sub(r'\s+', '', work_time)
                # link
                get_link = item_1.select_one('.t3_sb.underline_hover[href]').get('href')
                link = 'https://www.work24.go.kr' + get_link
                # print(link)

                rows.append({
                    '제목': job_title,
                    '위치': location,
                    '조건1': condition1,
                    '급여': salary,
                    '근무시간': work_time,
                    '회사이름': corp_name,
                    '링크': link
                })
        except Exception as e:
            print(f'Error work24: {e}, page: {page}, corp_name: {corp_name}')        
        time.sleep(1)
    df = pd.DataFrame(rows)
    return df
    # 3. 이름, 위치, 조건1(경력), 조건2(직무), 회사이름, 링크
    # return '교용24결과'

if __name__ == '__main__':
    # df = crawling_saramin('인공지능')
    # print(df[['회사이름', '위치']].head(5))
    # print(df[['회사이름', '조건1']].head(5))
    # print(df[['회사이름', '조건2']].head(5))
    # print(df[['회사이름', '회사이름']].head(5))
    # print(df[['회사이름', '링크']].head(5))
    # crawling_work24('AI')
    df = crawling_work24('AI')
    print(df[['회사이름', '제목']].head(5))
    print(df[['회사이름', '위치']].head(5))
    print(df[['회사이름', '조건1']].head(5))
    print(df[['회사이름', '급여']].head(5))
    print(df[['회사이름', '근무시간']].head(5))
    print(df[['회사이름', '링크']].head(5))