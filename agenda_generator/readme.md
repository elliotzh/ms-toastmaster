# Agenda 生成器
## Travis CI
1. 使用账号 mstoastmaster 登录 Github

2. 查看并根据最新的call role 结果更新[目标文件](https://github.com/eliiotz/ms-toastmaster/blob/master/agenda_generator/data/meeting.txt)。

   ![start-edit](img/doc.start-edit.png)

3. 修改目标文件（注意请保持格式一致并尽可能去除特殊字符），选中“创建新分支”，最后点击“propose file change”

   ![edit-file](img/doc.edit.png)

4. 使用默认设置创建Pull Request

   ![image-20200505093222349](img/doc.create-pr.png)

5. 此时系统会自动开始运行生成agenda的任务，请耐心等待

   ![image-20200505093515356](img/doc.wait-ci.png)

6. 点击commits以确认任务完成情况。任务完成后会生成一个名为"feat: auto-generated change"的commit。该commit生成后点击上方的链接（在新窗口中打开）前往feat分支以下载生成的agenda

   ![image-20200505094114175](img/doc.check-task-status.png)

7. 任务完成后，调整merge方式为squash and merge，完成Pull Request

   ![image-20200505094957990](img/doc.complete-pr.png)

8. 访问[该链接](https://htmlpreview.github.io/?https://github.com/elliotzh/ms-toastmaster/blob/master/agenda_generator/output/agenda.html)
对agenda进行预览和打印。

9. 如果agenda有误，回到1

10. 对于线下会议，记得打开腾讯问卷清空一下历史数据

   

