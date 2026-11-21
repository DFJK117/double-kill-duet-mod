local marginX = 4 local marginY = 2 local positionY = 185
function onCreate()
    addLuaScript('impostor/pita')
end
function onCreatePost()
    local creditsTable = {
        {"Double Kill", "DFJK117"}
    }
local songDisplayName = string.gsub(songName, '-', ' ')
    local creditText = 'DFJK117'
    for i = 1, #creditsTable do
        if songName == creditsTable[i][1] or songDisplayName == creditsTable[i][1] then
            songDisplayName = creditsTable[i][1]
            creditText = creditsTable[i][2]
            break
        end
    end
local fullText = songDisplayName .. '\n' .. creditText
    makeLuaText("infoCredit", fullText, 0, 0, positionY)
    setTextSize('infoCredit', 24)
    setTextAlignment('infoCredit', 'left')
    setTextFont("infoCredit", "liberbold.ttf")
    setTextBorder("infoCredit", 0.99, '000000')
    setObjectCamera("infoCredit", 'camOther')
    addLuaText("infoCredit")

    local bgWidth = getProperty('infoCredit.fieldWidth') + (marginX * 4)
    local bgHeight = getProperty('infoCredit.height') + (marginY * 4)

    makeLuaSprite('greyGraphic', '', -bgWidth - 50, positionY - marginY)
    makeGraphic('greyGraphic', math.floor(bgWidth), math.floor(bgHeight), 'FAFAFA')
    setProperty('greyGraphic.alpha', 0.2)
    setObjectCamera("greyGraphic", 'camOther')
    addLuaSprite('greyGraphic', false)
    setProperty('infoCredit.x', getProperty('greyGraphic.x') + marginX)
end

function onUpdate()
    if luaSpriteExists('greyGraphic') and luaTextExists('infoCredit') then
        setProperty('infoCredit.x', getProperty('greyGraphic.x') + marginX)
        setProperty('infoCredit.y', getProperty('greyGraphic.y') + marginY)
    end
end

function onCountdownTick(counter)
    if counter == 0 then
        doTweenX('greyX', 'greyGraphic', 0, 1, 'cubeOut')
        runTimer('adiosCreditos', 5)
    end
end

function onTimerCompleted(tag)
    if tag == 'adiosCreditos' then
        local exitPos = -getProperty('greyGraphic.width') - 50
        doTweenX('greyX', 'greyGraphic', exitPos, 1, 'cubeOut')
        runTimer('borrenlosss', 3)
    end
    
    if tag == 'borrenlosss' then
        removeLuaSprite('greyGraphic', true)
        removeLuaText('infoCredit', true)
    end
end