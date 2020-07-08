!function () {
    if (typeof data !== "object") {
        alert("Configure file is unavailabel")
        return
    }

    const buttonPause = $(".pause")
    const buttonTerminateMain = $(".terminate-main")
    const buttonTerminateSession = $(".terminate-session")
    const buttonStop = $(".stop")

    const mainTimer = $('.main-timer')
    const sessionTimer = $('.session-timer')
    const globalTimer = $('.global-timer')

    const mainTimerSpans = [$('.main-timer .second'), $('.main-timer .minute'), $('.main-timer .hour')]
    const sessionTimerSpans = [$('.session-timer .second'), $('.session-timer .minute'), $('.session-timer .hour')]
    const globalTimerSpans = [$('.global-timer .second'), $('.global-timer .minute'), $('.global-timer .hour')]

    // Read agenda list from JavaScript file
    // (not json) "resources/demo.js"
    // initialize DOM Element list in frontend
    const agendaListSelector = $('.agenda-list>ul')
    const liNodes = []
    function initializeAgendaList() {
        data.forEach((row, index) => {

            row.index = index
            row.session_sec_usage = 0
            row.events_sec_usage = []

            let node = $(`<li index="${index}"></li>`),
                event_node = $("<span class=\"event\"></span>").text(row.event),
                member_node = $("<span class=\"member\"></span>").text(row.member),
                role_node = $("<span class=\"role\"></span>").text(row.role),
                usage_node = $("<span class=\"usage\"></span>")

            node.append(event_node)
            node.append("<br>")
            node.append(member_node)
            node.append(" | ")
            node.append(role_node)
            node.append("<br>")
            node.append(usage_node)

            agendaListSelector.append(node)
            liNodes.push(node)
        })
    }
    initializeAgendaList()

    // Switch current event to next one
    function setCurrentSession(index) {
        if (index >= data.length) return
        currentRowIndex = index
        $('.agenda-list li').removeClass("current")
        $(`.agenda-list li[index=${index}]`).addClass("current")
    }

    let isPause = false

    // current event time usage
    let currentMainCounter = 0

    // current session (multiple events) time usage
    let currentSessionCounter = 0

    // all time usage
    let currentGlobalCounter = 0

    let timeInterval = null

    let currentRowIndex = null

    function displayCounter(selector, value, spans) {
        let second = (value % 60) >> 0,
            minute = (value / 60 % 60) >> 0,
            hour = (value / 3600) >> 0

        if (hour) {
            hour = String(hour).padStart(2, "0")
            selector.addClass("extra")
        }
        else selector.removeClass("extra")

        spans[0].text(String(second).padStart(2, '0'))
        spans[1].text(String(minute).padStart(2, '0'))
        spans[2].text(hour)

        return [second, minute]
    }

    // callback function on every second
    function onTick() {
        if (isPause) return
        currentMainCounter += 1
        currentSessionCounter += 1
        currentGlobalCounter += 1

        let [event_seconds, event_minutes] = displayCounter(mainTimer, currentMainCounter, mainTimerSpans)
        displayCounter(sessionTimer, currentSessionCounter, sessionTimerSpans)
        displayCounter(globalTimer, currentGlobalCounter, globalTimerSpans)

        const limits = data[currentRowIndex].limits
        if (limits[2] >= 0 && (event_minutes > limits[2] || (event_minutes === limits[2] && event_seconds >= 30))) {
            mainTimer.addClass('alert-4')
        }
        else if (limits[2] >= 0 && event_minutes >= limits[2]) {
            mainTimer.addClass('alert-3')
        }
        else if (limits[1] >= 0 && event_minutes >= limits[1]) {
            mainTimer.addClass('alert-2')
        }
        else if (limits[0] >= 0 && event_minutes >= limits[0]) {
            mainTimer.addClass('alert-1')
        }
    }

    function startTimer() {
        buttonStop.text("Stop Timer")
        buttonStop.off('click')
        buttonStop.on('click', stopTimer)
        timeInterval = setInterval(onTick, 1000)
        setCurrentSession(0)
    }
    function stopTimer() {
        clearInterval(timeInterval)
        console.log(data)
    }
    buttonStop.on('click', startTimer)

    function pause() {
        isPause = !isPause
        if (isPause) buttonPause.addClass('paused').text('Paused')
        else buttonPause.removeClass('paused').text('Pause')
    }
    buttonPause.on('click', pause)

    function terminateEvent() {
        if (currentRowIndex === null || currentRowIndex < 0) return
        const row = data[currentRowIndex]

        row.events_sec_usage.push(currentMainCounter)
        displayCounter(mainTimer, 0, mainTimerSpans)
        currentMainCounter = 0

        mainTimer
        .removeClass('alert-4')
        .removeClass('alert-3')
        .removeClass('alert-2')
        .removeClass('alert-1')
    }
    buttonTerminateMain.on('click', terminateEvent)

    function terminateSession() {
        if (currentRowIndex === null || currentRowIndex < 0) return

        const row = data[currentRowIndex]

        terminateEvent()
        row.session_sec_usage = currentSessionCounter
        displayCounter(sessionTimer, 0, sessionTimerSpans)
        currentSessionCounter = 0

        liNodes[currentRowIndex].children('.usage').text(
            row.events_sec_usage.map(counterToString).join(', ')
        )

        setCurrentSession(currentRowIndex + 1)
        if (currentRowIndex === data.length - 1) {
            stopTimer()
        }
    }
    buttonTerminateSession.on('click', terminateSession)


    function counterToString(value) {
        let second = (value % 60) >> 0,
            minute = (value / 60 % 60) >> 0,
            hour = (value / 3600) >> 0
        let list = [minute, second]
        if (hour > 0) list = [hour, ...list]

        list = list.map(x => String(x).padStart(2, '0'))
        return list.join(':')
    }

}();