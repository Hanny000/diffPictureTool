import pywebio
from pywebio.input import input,file_upload, select, actions, input_update, checkbox, input_group
from pywebio.output import put_table, span, put_html, put_buttons, use_scope, put_loading, popup, PopupSize
from pywebio.session import run_js

from fontend.format_converter import bytes_to_base64
from fontend.request import send_diff_pic_request, send_load_project_request, send_load_history_pic_request,save_pic_request

global pa


'''
这个方法用于设置结果展示页面的表格，
result:测试结果，参数 passed 和failed两种
pic_name:测试的图片的名称
byte_of_old_pic:旧的图的二进制代码（因为最后展示在html上的时候图片文件必须转成二进制的代码才能被解析出来）
byte_of_new_pic:新的图的二进制代码（因为最后展示在html上的时候图片文件必须转成二进制的代码才能被解析出来）

这里还用到了pywebio的https://pywebio.readthedocs.io/zh_CN/latest/output.html#output-scope
use_scope用于把pass和failed的结果都放进这个标签内,并且给他赋值一个id，方便我们后期去管理展示，比如只显示pass的和只显示failed的结果
<div id="pywebio-scope-passed"> pass的结果的html代码 </div>
我们后面就可以通过id来控制对应pass和fail tab的展示和消失

put_table用于生成表格，具体用法参见 https://pywebio.readthedocs.io/zh_CN/latest/output.html#pywebio.output.put_table

这边还用到了一个 put_html，是直接插入html的代码，主要给pass和fail的那一格加颜色，加红色和绿色，具体用法参见 https://pywebio.readthedocs.io/zh_CN/latest/output.html#pywebio.output.put_html

'''
def set_result_table(result,pic_name,base64_of_old_pic,base64_of_new_pic):
    if result == "pass":
        with use_scope('passed'):
            put_table([[span(pic_name, col=3)], [put_html("<td style='color:#ffffff' bgcolor='#28a745'> pass</td>"),
                                             put_html("<img src = 'data:image/png;base64,{0}'>".format(base64_of_old_pic)),
                                             put_html("<img src = 'data:image/png;base64,{0}'>".format(base64_of_new_pic))]],scope='passed')
    elif result == "fail":
        with use_scope('failed'):
            put_table([[span(pic_name, col=3)], [put_html("<td style='color:#ffffff' bgcolor='#dc354'> fail</td>"),
                                             put_html("<img src = 'data:image/png;base64,{0}'>".format(base64_of_old_pic)),
                                             put_html("<img src = 'data:image/png;base64,{0}'>".format(base64_of_new_pic))]],scope='failed')


def bmi():
    all_result = []
    history_pic = {}
    '''
    confirm对应的是第一个页面，就是让你选择是新传图还是用旧的release图
    action用法参见 https://pywebio.readthedocs.io/zh_CN/latest/input.html?highlight=actions#pywebio.input.actions
    '''

    confirm = actions('Upload new or choose history?', ['new', 'history'],
                      help_text='Unrecoverable after file deletion')

    '''
    all_history 是一个用于存放历史release的字典,会遍历读取history这个文件夹下的所有图片目录
    生成的字典如下
    {'mThor': ['1.1.1', '1.1.2'], 'SW': ['1.1.1']}
    action用法参见 https://pywebio.readthedocs.io/zh_CN/latest/input.html?highlight=actions#pywebio.input.actions
    '''

    info = None
    all_history = send_load_project_request().json()
    projects_name = list(all_history.keys())

    '''
    如果选择new，就进入到new的选择逻辑里，
    input_group里的就是页面上显示的控件，这边就不详细介绍了，可以查阅文档
    '''
    if confirm == 'new':
        info = input_group("Pic", [
            file_upload("input old image:", name="old_images", accept="image/*", multiple=True),
            file_upload("input new image:", name="new_images", accept="image/*", multiple=True),
            checkbox(options=['Save pic'],name="save_pic"),
            select("Select project:", options=["SW","mThor"], name="project"),
            input('Input your release', name='release'),

        ])

        '''
        如果save pic被勾选则会保存你这次提交的new里的图片，需要选择项目和填入release
        todo：如果勾选了save，又没填release要抛个提示，还有已存在历史图了是否要更新。
        '''
        if len(info["save_pic"]) > 0:
            base64_of_images = {}
            for new_image in info["new_images"]:
                base64_of_images[new_image["filename"]] = bytes_to_base64(new_image["content"])
            response = save_pic_request(base64_of_images, info["project"], info["release"]).status_code
            if response == 401:
                popup('tip', 'The history pic already exists', size=PopupSize.SMALL)

        '''
        这边就是在读取所有旧图的二进制代码并存放到
        history_pic这个字典里，结果如下
            {'test1.png': "xxx(二进制代码)", 'test2.png': "xxx(二进制代码)"}
        '''
        for old_image in info["old_images"]:
            history_pic[old_image["filename"]] = bytes_to_base64(old_image['content'])


    elif confirm == 'history':
        info = input_group("User info", [
            select("Select project:", options=projects_name, name="project",
                   onchange=lambda project_name: input_update("release", options=all_history[project_name])),
            select("Release", options=all_history[projects_name[0]], name="release"),
            file_upload("input new image:", name="new_images", accept="image/*", multiple=True)
        ])
        history_pic = send_load_history_pic_request(info["project"],info["release"]).json()

    def all():
        run_js('''document.getElementById("pywebio-scope-failed").style.display =""''')
        run_js('''document.getElementById("pywebio-scope-passed").style.display =""''')

    def passed():
        run_js('''document.getElementById("pywebio-scope-passed").style.display =""''')
        run_js('''document.getElementById("pywebio-scope-failed").style.display ="none"''')

    def failed():
        run_js('''document.getElementById("pywebio-scope-passed").style.display ="none"''')
        run_js('''document.getElementById("pywebio-scope-failed").style.display =""''')



    with put_loading(shape='border', color='dark'):
        passed_count = 0
        failed_count = 0
        for new_image in info["new_images"]:
            for pic_name in history_pic.keys():
                if pic_name == new_image["filename"]:
                    result = send_diff_pic_request(pic_name, history_pic[pic_name], bytes_to_base64(new_image['content']))
                    if result.json().get("test_result") == "pass":
                        passed_count += 1
                    elif result.json().get("test_result") == "fail":
                        failed_count += 1
                    all_result.append(result)
        put_buttons([{'label': 'all', 'value': "I'm success", 'color': "primary"},
                     {'label': '%s passed' % passed_count, 'value': "I'm success", 'color': "success"},
                     {'label': '%s failed' % failed_count, 'value': "I'm success", 'color': "danger"}], onclick=[all, passed, failed]).show()

        for result in all_result:
            set_result_table(result.json().get("test_result"),
                             result.json().get("pic_name"),
                             result.json().get("base64_of_old_pic"),
                             result.json().get("base64_of_res"))


if __name__ == '__main__':
    pywebio.start_server(bmi, port=80)
