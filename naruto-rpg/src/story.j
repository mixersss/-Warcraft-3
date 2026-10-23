// First chapter: bounded state and one shared 0.5s heartbeat.
function StoryTeam takes integer p returns integer
    return (p-ModuloInteger(p,3))/3
endfunction
function StorySay takes integer t, string text returns nothing
    local integer p=t*3
    loop
        exitwhen p>=t*3+3
        if GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
            call DisplayTimedTextToPlayer(Player(p),0.,0.,18.,text)
        endif
        set p=p+1
    endloop
endfunction
function StoryLeader takes integer t returns unit
    local integer p=t*3
    local unit fallback=null
    loop
        exitwhen p>=t*3+3
        if FoundationAlive(Hero[p]) then
            if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER then
                return Hero[p]
            endif
            set fallback=Hero[p]
        endif
        set p=p+1
    endloop
    return fallback
endfunction
function StoryGoal takes integer t returns string
    if StoryStage[t]>=9 then
        return CampaignName[StoryStage[t]]+". "+CampaignIntro[StoryStage[t]]+" |n-go: к цели; -follow: прикрытие; -retreat: отход. В убежище смерть окончательная!"
    endif
    if StoryStage[t]==0 then
        return "Наставник: выберите героя (-heroes, -hero 1..12), изучите техники кнопкой +. Противники уже в лесу; начало через 30 секунд или раньше по -go. -shop: снабжение."
    elseif StoryStage[t]==1 then
        return "Миссия 1/4: победите семь вражеских ниндзя в лесу. Всего в каждой локации 14 ниндзя, как в исходной карте."
    elseif StoryStage[t]==2 then
        return "Миссия 2/4: зачистите оставшихся ниндзя в лесу и подготовьтесь к бою с Хаку."
    elseif StoryStage[t]==3 then
        return "Миссия 3/4: победите Хаку. Выходите из отмеченных зон ледяных игл."
    elseif StoryStage[t]==4 then
        return "Миссия 4/4: победите Забузу у моста. Уклоняйтесь от водного удара; во второй фазе он атакует чаще."
    endif
    if StoryStage[t]==5 then
        return "Мост спасён! Ждём возвращения остальных отрядов, затем экзамен с вопросами и Лес смерти. Можно купить снаряжение: -shop."
    elseif StoryStage[t]==6 then
        return "Экзамен Ибики: пять вопросов. Ответьте цифрой 1..4 в чат. Одна попытка на вопрос; верный ответ даёт 120 опыта."
    elseif StoryStage[t]==7 then
        return "Лес смерти: найдите свитки Неба и Земли. Оба носителя должны подойти к башне в последние две минуты. До конца: "+I2S(R2I(RMaxBJ(0.,ExamEndAt-TimeNow)))+" сек. -go: поиск; -follow: рядом с вами; -retreat: к входу."
    endif
    return "Экзамен со свитками завершён. Предварительные поединки будут следующим этапом."
endfunction
function StoryReward takes integer t, integer gold, integer xp returns nothing
    local integer p=t*3
    loop
        exitwhen p>=t*3+3
        if Hero[p]!=null then
            call SetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)+gold)
            // First forest uses native kill XP, as in the source; no synthetic quest XP.
        endif
        set p=p+1
    endloop
endfunction
function StoryPopulate takes nothing returns nothing
    local integer t=(StoryPopulateCursor-ModuloInteger(StoryPopulateCursor,16))/16
    local integer n=ModuloInteger(StoryPopulateCursor,16)
    local integer j=t*18+n
    local integer raw='re01'
    local unit u=null
    if t>=4 then
        call PauseTimer(StoryPopulateClock)
        call DestroyTimer(StoryPopulateClock)
        set StoryPopulateClock=null
        return
    endif
    if StoryMembers[t]>0 then
        set EnemyKind[j]=1
        if n==14 then
            set raw='re03'
            set EnemyKind[j]=3
        elseif n==15 then
            set raw='re04'
            set EnemyKind[j]=4
        endif
        set u=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),raw,EnemySpawnX[j],EnemySpawnY[j],180.)
        if n==14 then
            call NPCSourceInit()
        endif
        call SetUnitCreepGuard(u,false)
        call RemoveGuardPosition(u)
        set StoryEnemy[j]=u
        set EnemyNext[j]=8.+n
        set EnemyPrisonAt[j]=12.
        if n==15 then
            set StoryBoss[t]=u
        endif
    endif
    set StoryPopulateCursor=StoryPopulateCursor+1
    set u=null
endfunction
function StoryStartStage takes integer t returns nothing
    if StoryStage[t]>=5 then
        return
    endif
    set StoryStage[t]=StoryStage[t]+1
    set StoryAdvanceAt[t]=0.
    if StoryStage[t]==3 then
        call StorySay(t,"Хаку: Я не позволю вам пройти. Для того, кто мне дорог, я готов стать оружием. |nНаставник: Держитесь вместе и следите за ледяными метками!")
    elseif StoryStage[t]==4 then
        call StorySay(t,"Забуза: Вы добрались до моста... Но дальше вас не пропустит демон Скрытого Тумана. |nНаставник: У него есть рывок, рассечение, водяная тюрьма и клоны. Прикройте друг друга!")
    else
        call StorySay(t,"Наставник: В лесу 14 ниндзя. Очищаем тропы вместе, не оставляйте товарищей в одиночестве.")
    endif
    call StorySay(t,StoryGoal(t)+" |n-go: боты идут к цели; -follow: прикрывают вас; -retreat: отход; -quest: задание.")
endfunction
function StoryEnemyCandidate takes unit enemy, unit candidate returns boolean
    return FoundationAlive(candidate) and not IsUnitHidden(candidate) and not IsUnitPaused(candidate) and GetUnitAbilityLevel(candidate,'Avul')==0 and IsUnitEnemy(candidate,GetOwningPlayer(enemy))
endfunction
function StoryEnemyTarget takes integer t, unit enemy, unit leader returns unit
    local integer p=t*3
    local integer n=0
    local unit candidate=null
    local real dx=0.
    local real dy=0.
    local real distance=999999999.
    set StoryTargetResult=null
    loop
        exitwhen p>=t*3+3
        set n=-1
        loop
            exitwhen n>=3
            if n<0 then
                set candidate=Hero[p]
            else
                set candidate=Companion[p*3+n]
            endif
            if StoryEnemyCandidate(enemy,candidate) then
                set dx=GetUnitX(candidate)-GetUnitX(enemy)
                set dy=GetUnitY(candidate)-GetUnitY(enemy)
                if dx*dx+dy*dy<distance then
                    set distance=dx*dx+dy*dy
                    set StoryTargetResult=candidate
                endif
            endif
            set n=n+1
        endloop
        set p=p+1
    endloop
    if StoryMentorsReleased and StoryEnemyCandidate(enemy,StoryMentor[t]) then
        set dx=GetUnitX(StoryMentor[t])-GetUnitX(enemy)
        set dy=GetUnitY(StoryMentor[t])-GetUnitY(enemy)
        if dx*dx+dy*dy<distance then
            set StoryTargetResult=StoryMentor[t]
        endif
    endif
    set candidate=null
    return StoryTargetResult
endfunction
function StoryEnemyCast takes integer j, unit target returns nothing
    local unit u=StoryEnemy[j]
    local real dx=GetUnitX(target)-GetUnitX(u)
    local real dy=GetUnitY(target)-GetUnitY(u)
    if EnemyKind[j]==3 then
        call NPCFirstHaku(u)
    endif
    if EnemyKind[j]==4 and TimeNow>=EnemyBlinkAt[j] and dx*dx+dy*dy>500.*500. and GetUnitState(u,UNIT_STATE_MANA)>=10. then
        if IssuePointOrder(u,"blink",GetUnitX(target),GetUnitY(target)) then
            set EnemyBlinkAt[j]=TimeNow+5.
            set EnemyNext[j]=TimeNow+1.
            set u=null
            return
        endif
    endif
    call IssueTargetOrder(u,"attack",target)
    set EnemyNext[j]=TimeNow+3.
    set u=null
endfunction
function StoryEnemyHit takes integer j returns nothing
    local integer t=(j-ModuloInteger(j,18))/18
    local integer p=t*3
    local integer stage=EnemyKind[j]
    local real damage=45.+stage*25.
    local real radius=180.+stage*25.
    local real dx=0.
    local real dy=0.
    if EnemyMark[j]!=null then
        call DestroyEffect(EnemyMark[j])
        set EnemyMark[j]=null
    endif
    set EnemyPending[j]=0.
    if not FoundationAlive(StoryEnemy[j]) then
        return
    endif
    if stage==3 then
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Undead\\FrostNova\\FrostNovaTarget.mdl",EnemyX[j],EnemyY[j]))
    else
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Other\\CrushingWave\\CrushingWaveDamage.mdl",EnemyX[j],EnemyY[j]))
    endif
    loop
        exitwhen p>=t*3+3
        if FoundationAlive(Hero[p]) then
            set dx=GetUnitX(Hero[p])-EnemyX[j]
            set dy=GetUnitY(Hero[p])-EnemyY[j]
            if dx*dx+dy*dy<radius*radius then
                call UnitDamageTarget(StoryEnemy[j],Hero[p],damage,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
                if stage==3 then
                    call SetUnitState(Hero[p],UNIT_STATE_MANA,RMaxBJ(0.,GetUnitState(Hero[p],UNIT_STATE_MANA)-60.))
                endif
            endif
        endif
        set p=p+1
    endloop
    if StoryMentorsReleased and FoundationAlive(StoryMentor[t]) then
        set dx=GetUnitX(StoryMentor[t])-EnemyX[j]
        set dy=GetUnitY(StoryMentor[t])-EnemyY[j]
        if dx*dx+dy*dy<radius*radius then
            call UnitDamageTarget(StoryEnemy[j],StoryMentor[t],damage,false,false,ATTACK_TYPE_NORMAL,DAMAGE_TYPE_MAGIC,WEAPON_TYPE_WHOKNOWS)
        endif
    endif
endfunction
function StoryObjectiveEnemy takes integer t, integer n returns boolean
    if StoryStage[t]<=2 then
        return n<14
    elseif StoryStage[t]==3 then
        return n==14
    endif
    return n>=15
endfunction
function StoryNearest takes integer t, unit actor returns unit
    local integer n=0
    local integer j=0
    local real distance=999999999.
    local real dx=0.
    local real dy=0.
    local unit result=null
    loop
        exitwhen n>=18
        set j=t*18+n
        if StoryObjectiveEnemy(t,n) and FoundationAlive(StoryEnemy[j]) then
            set dx=GetUnitX(actor)-GetUnitX(StoryEnemy[j])
            set dy=GetUnitY(actor)-GetUnitY(StoryEnemy[j])
            if dx*dx+dy*dy<distance then
                set distance=dx*dx+dy*dy
                set result=StoryEnemy[j]
            endif
        endif
        set n=n+1
    endloop
    return result
endfunction
function StoryDrop takes integer j returns nothing
    local integer roll=0
    local integer raw=0
    if EnemyLootRolled[j] or StoryEnemy[j]==null then
        return
    endif
    set EnemyLootRolled[j]=true
    // QOV is attached to first-forest ordinary ninjas, not Haku/Zabuza/clones.
    if EnemyKind[j]!=1 and EnemyKind[j]!=2 then
        return
    endif
    set roll=GetRandomInt(1,100)
    if roll<=10 then
        set raw='Nlra'
    elseif roll<=20 then
        set raw='Nlpi'
    elseif roll<=27 then
        set raw='Nlsh'
    elseif roll<=35 then
        set raw='Nnot'
    elseif roll<=43 then
        set raw='Nlku'
    elseif roll<=45 then
        set raw='Nlga'
    elseif roll<=55 then
        set raw='Nlne'
    endif
    if raw!=0 then
        set StoryLoot[j]=CreateItem(raw,GetUnitX(StoryEnemy[j]),GetUnitY(StoryEnemy[j]))
    endif
endfunction
// One reused spatial rect, synchronous callbacks, no tracking every dropped item.
function StoryStatScrollScan takes nothing returns nothing
    local item it=GetEnumItem()
    local integer raw=GetItemTypeId(it)
    local integer p=StatLootPlayer
    local real dx=GetItemX(it)-GetUnitX(Hero[p])
    local real dy=GetItemY(it)-GetUnitY(Hero[p])
    if (raw=='Nsht' or raw=='Nsch' or raw=='Nsta') and not IsItemOwned(it) and GetWidgetLife(it)>.405 and IsItemVisible(it) and IsVisibleToPlayer(GetItemX(it),GetItemY(it),Player(p)) and TreeJumpInside(p,GetItemX(it),GetItemY(it)) and (it!=ExamBotAvoidItem[p] or TimeNow>=ExamBotItemAvoidUntil[p]) then
        if dx*dx+dy*dy<StatLootDistance then
            set StatLootBest=it
            set StatLootDistance=dx*dx+dy*dy
        endif
    endif
    set it=null
endfunction
function StoryStatLootBot takes integer p, unit enemy returns boolean
    local real x=GetUnitX(Hero[p])
    local real y=GetUnitY(Hero[p])
    local real dx=0.
    local real dy=0.
    local item target=null
    local boolean ordered=false
    if not FoundationAlive(Hero[p]) or TimeNow<VisualChannelUntil[p] or ComboLeft[p]>0 or StoryRetreat[StoryTeam(p)] or CampaignTransition or CampaignStage==9 or CampaignStage==11 or (StoryStage[StoryTeam(p)]==7 and ExamTowerOpen) or GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.25 then
        return false
    endif
    if FoundationAlive(enemy) then
        set dx=GetUnitX(enemy)-x
        set dy=GetUnitY(enemy)-y
        if dx*dx+dy*dy<900.*900. then
            return false
        endif
    endif
    if StatLootRect==null then
        set StatLootRect=Rect(0.,0.,0.,0.)
    endif
    call SetRect(StatLootRect,x-650.,y-650.,x+650.,y+650.)
    set StatLootPlayer=p
    set StatLootBest=null
    set StatLootDistance=650.*650.
    call EnumItemsInRect(StatLootRect,null,function StoryStatScrollScan)
    set target=StatLootBest
    set StatLootBest=null
    if target!=null then
        // Native tst2 powerups apply their actual +6 and work with six carried items.
        set ordered=IssueTargetOrder(Hero[p],"smart",target)
        if ordered then
            set BotNextCast[p]=TimeNow+.75
        endif
    endif
    set target=null
    return ordered
endfunction
function StoryLootBot takes integer p, unit enemy returns boolean
    local integer n=0
    local integer t=StoryTeam(p)
    local item carried=null
    local integer raw=0
    local boolean free=false
    local real dx=0.
    local real dy=0.
    if TimeNow>=BotUseItemAt[p] then
        loop
            exitwhen n>=6
            set carried=UnitItemInSlot(Hero[p],n)
            if carried==null then
                set free=true
            else
                set raw=GetItemTypeId(carried)
                if (raw=='Nlra' or raw=='Nlpi') and (GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.6 or GetUnitState(Hero[p],UNIT_STATE_MANA)<GetUnitState(Hero[p],UNIT_STATE_MAX_MANA)*.3) then
                    if UnitUseItem(Hero[p],carried) then
                        set BotUseItemAt[p]=TimeNow+8.
                        set carried=null
                        return true
                    endif
                elseif raw=='Nnot' and FoundationAlive(enemy) then
                    set dx=GetUnitX(enemy)-GetUnitX(Hero[p])
                    set dy=GetUnitY(enemy)-GetUnitY(Hero[p])
                    if dx*dx+dy*dy<550.*550. and UnitUseItemPoint(Hero[p],carried,GetUnitX(Hero[p])+dx*.5,GetUnitY(Hero[p])+dy*.5) then
                        set BotUseItemAt[p]=TimeNow+8.
                        set carried=null
                        return true
                    endif
                elseif (raw=='Nlku' or raw=='Nlsh' or raw=='Nlne') and FoundationAlive(enemy) then
                    set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
                    set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
                    if dx*dx+dy*dy<500.*500. and UnitUseItemTarget(Hero[p],carried,enemy) then
                        set BotUseItemAt[p]=TimeNow+3.
                        set carried=null
                        return true
                    endif
                endif
            endif
            set n=n+1
        endloop
        if free then
            set n=t*18
            loop
                exitwhen n>=t*18+18
                set carried=StoryLoot[n]
                if carried!=null and GetItemTypeId(carried)!=0 and not IsItemOwned(carried) then
                    set dx=GetUnitX(Hero[p])-GetItemX(carried)
                    set dy=GetUnitY(Hero[p])-GetItemY(carried)
                    if dx*dx+dy*dy<650.*650. then
                        set carried=null
                        return IssueTargetOrder(Hero[p],"smart",StoryLoot[n])
                    endif
                endif
                set n=n+1
            endloop
        endif
    endif
    set carried=null
    return false
endfunction
function StoryShopFor takes integer p returns unit
    local integer j=0
    local unit result=null
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    if (CampaignStage!=10 and CampaignStage!=12) or CampaignTransition then
        return null
    endif
    loop
        exitwhen j>=4
        if StoryShop[j]!=null then
            set dx=GetUnitX(Hero[p])-GetUnitX(StoryShop[j])
            set dy=GetUnitY(Hero[p])-GetUnitY(StoryShop[j])
            if dx*dx+dy*dy<best then
                set result=StoryShop[j]
                set best=dx*dx+dy*dy
            endif
        endif
        set j=j+1
    endloop
    return result
endfunction
function StoryShopsClose takes nothing returns nothing
    local integer j=0
    loop
        exitwhen j>=4
        if StoryShop[j]!=null then
            call RemoveUnit(StoryShop[j])
            set StoryShop[j]=null
        endif
        set j=j+1
    endloop
    if StoryShopSales!=null then
        call DestroyTrigger(StoryShopSales)
        set StoryShopSales=null
    endif
endfunction
function StoryHasItemSpace takes integer p returns boolean
    local integer k=0
    loop
        exitwhen k>=6
        if UnitItemInSlot(Hero[p],k)==null then
            return true
        endif
        set k=k+1
    endloop
    return false
endfunction
function StoryStatChoice takes integer p returns integer
    local integer role=HeroRole[p]
    if role==0 or role==1 then
        return 7
    elseif role==2 or role==6 or role==9 or role==10 then
        return 8
    endif
    return 9
endfunction
function StoryCanCarryChoice takes integer p, integer choice returns boolean
    return StoryHasItemSpace(p) or (choice>=7 and choice<=9)
endfunction
function StoryChooseItem takes integer p returns integer
    local integer choice=0
    local integer slot=0
    local integer role=HeroRole[p]
    // Native stat powerups are consumed on purchase, including with six carried items.
    if not StoryHasItemSpace(p) or (StoryBought[p]>=3 and ModuloInteger(StoryBought[p],4)==3) then
        return StoryStatChoice(p)
    endif
    set choice=ModuloInteger(StoryBought[p],3)
    if choice==1 then
        set choice=4
    elseif choice==2 then
        if role==2 or role==6 or role==9 or role==10 or role==11 then
            set choice=3
        elseif role==0 or role==3 or role==7 then
            set choice=1
        else
            set choice=2
        endif
    endif
    if choice==0 then
        set slot=0
        loop
            exitwhen slot>=6
            if GetItemTypeId(UnitItemInSlot(Hero[p],slot))=='Nlga' then
                set choice=6
            elseif GetItemTypeId(UnitItemInSlot(Hero[p],slot))=='Nlca' then
                set choice=StoryStatChoice(p)
                exitwhen true
            endif
            set slot=slot+1
        endloop
    endif
    return choice
endfunction
function StoryBuy takes integer p returns nothing
    local integer t=StoryTeam(p)
    local integer slot=0
    local integer choice=0
    local integer role=HeroRole[p]
    local boolean full=true
    local unit shop=StoryShopFor(p)
    // Preparation must leave every hero inventory empty; purchases begin during play.
    if shop==null or (CampaignStage!=10 and CampaignStage!=12) or CampaignTransition then
        return
    endif
    if TimeNow<StoryBuyAt[p] or GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)<30 then
        return
    endif
    loop
        exitwhen slot>=6
        if UnitItemInSlot(Hero[p],slot)==null then
            set full=false
        endif
        set slot=slot+1
    endloop
    set choice=StoryChooseItem(p)
    if full and not StoryCanCarryChoice(p,choice) then
        return
    endif
    if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=StoryPrice[choice] then
        call IssueNeutralTargetOrder(Player(p),shop,"neutralinteract",Hero[p])
        call IssueNeutralImmediateOrderById(Player(p),shop,StoryItem[choice])
        set StoryBuyAt[p]=TimeNow+4.
    endif
    set shop=null
endfunction
function StoryOnBuy takes nothing returns nothing
    local unit buyer=GetBuyingUnit()
    local integer p=GetPlayerId(GetOwningPlayer(buyer))
    if p<12 and buyer==Hero[p] then
        set StoryBought[p]=StoryBought[p]+1
    endif
    set buyer=null
endfunction
function StoryShopsOpen takes nothing returns nothing
    local integer j=0
    if CampaignStage!=10 and CampaignStage!=11 and CampaignStage!=12 then
        return
    endif
    call StoryShopsClose()
    set StoryShopSales=CreateTrigger()
    call TriggerAddAction(StoryShopSales,function StoryOnBuy)
    loop
        exitwhen j>=4
        set StoryShop[j]=CreateUnit(Player(14),'rqsh',StoryShopX[j],StoryShopY[j],270.)
        call TriggerRegisterUnitEvent(StoryShopSales,StoryShop[j],EVENT_UNIT_SELL_ITEM)
        set j=j+1
    endloop
endfunction

function StoryActivate takes integer t, boolean march returns nothing
    local integer n=t*3
    set StoryStarted[t]=true
    set StoryMarch[t]=march
    set StoryRetreat[t]=false
    loop
        exitwhen n>=t*3+3
        set StoryBotOrderAt[n]=0.
        set n=n+1
    endloop
endfunction
// NEXT_CHAPTER_RUNTIME
function StoryFountainFor takes integer p returns unit
    local integer j=0
    local unit nearest=null
    local real best=999999999.
    local real dx=0.
    local real dy=0.
    if (CampaignStage!=10 and CampaignStage!=12) or CampaignTransition then
        return null
    endif
    loop
        exitwhen j>=4
        if VillageFountain[j]!=null then
            set dx=GetUnitX(VillageFountain[j])-GetUnitX(Hero[p])
            set dy=GetUnitY(VillageFountain[j])-GetUnitY(Hero[p])
            if dx*dx+dy*dy<best then
                set best=dx*dx+dy*dy
                set nearest=VillageFountain[j]
            endif
        endif
        set j=j+1
    endloop
    return nearest
endfunction
function StoryCommand takes integer p, string msg returns nothing
    local integer t=StoryTeam(p)
    local integer n=0
    local unit goal=null
    local unit shop=null
    if msg=="-go" then
        if StoryStage[t]==0 then
            call StoryStartStage(t)
        endif
        call StoryActivate(t,true)
        call StorySay(t,"Отряд: Принято, идём к цели вместе. Прикрываем товарищей!")
    elseif msg=="-follow" then
        set StoryMarch[t]=false
        set StoryRetreat[t]=false
        call StorySay(t,"Отряд: Держимся рядом с тобой и помогаем в ближайшем бою.")
    elseif msg=="-retreat" then
        set StoryRetreat[t]=true
        set StoryMarch[t]=false
        call StorySay(t,"Отряд: Отходим к наставнику, восстанавливаем здоровье и чакру.")
    elseif msg=="-quest" then
        call StorySay(t,StoryGoal(t))
        if StoryStage[t]>=9 then
            set goal=CampaignNearest(p)
            if goal!=null then
                call PingMinimapEx(GetUnitX(goal),GetUnitY(goal),5.,255,210,50,false)
            endif
        elseif StoryStage[t]==7 then
            call PingMinimapEx(ExamTowerX,ExamTowerY,5.,255,210,50,false)
            if ExamHas(t,'Eshe') then
                call StorySay(t,"Отряд: Свиток Неба при нас.")
            else
                call StorySay(t,"Отряд: Нужен свиток Неба.")
            endif
            if ExamHas(t,'Esea') then
                call StorySay(t,"Отряд: Свиток Земли при нас.")
            else
                call StorySay(t,"Отряд: Нужен свиток Земли.")
            endif
        elseif StoryStage[t]>0 and StoryStage[t]<5 then
            set goal=StoryNearest(t,Hero[p])
            if goal!=null then
                call PingMinimapEx(GetUnitX(goal),GetUnitY(goal),5.,255,210,50,false)
            endif
            set goal=null
        endif
    elseif msg=="-kabuto" then
        if CampaignStage==26 and p==CampaignSasukePlayer then
            call SelectUnitForPlayerSingle(CampaignActor[0],Player(p))
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(CampaignActor[0]),GetUnitY(CampaignActor[0]),1.)
        elseif CampaignStage==12 and HeroRole[p]==10 and CampaignVillageKabuto!=null then
            call SelectUnitForPlayerSingle(CampaignVillageKabuto,Player(p))
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(CampaignVillageKabuto),GetUnitY(CampaignVillageKabuto),1.)
        endif
    elseif msg=="-kabutooff" or msg=="-kabutoon" then
        if (CampaignStage==26 and p==CampaignSasukePlayer) or (CampaignStage==12 and HeroRole[p]==10) then
            set CampaignKabutoAI=msg=="-kabutoon"
        endif
    elseif msg=="-fountain" then
        set goal=StoryFountainFor(p)
        if goal!=null then
            call SelectUnitForPlayerSingle(goal,Player(p))
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(goal),GetUnitY(goal),1.)
            call PingMinimapEx(GetUnitX(goal),GetUnitY(goal),5.,80,200,255,false)
            call DisplayTimedTextToPlayer(Player(p),0.,0.,10.,"Фонтан Конохи: подведите героя для восстановления HP и чакры. -camera: вернуться к герою.")
        else
            call DisplayTimedTextToPlayer(Player(p),0.,0.,10.,"Фонтаны Конохи доступны при поиске Джирайи и во время вторжения. В Лесу смерти работают два отдельных фонтана.")
        endif
        set goal=null
    elseif msg=="-shop" then
        set goal=StoryShopFor(p)
        if goal!=null then
            call SelectUnitForPlayerSingle(goal,Player(p))
            call PanCameraToTimedForPlayer(Player(p),GetUnitX(goal),GetUnitY(goal),1.)
            call DisplayTimedTextToPlayer(Player(p),0.,0.,10.,"Снабжение Конохи: подведите своего героя и купите предмет кнопкой магазина. -camera: вернуться к герою.")
        else
            call DisplayTimedTextToPlayer(Player(p),0.,0.,8.,"Магазины Конохи открыты при поиске Джирайи и во время вторжения. До посещения города снаряжение выпадает с врагов.")
        endif
        set goal=null
    elseif msg=="-camera" and Hero[p]!=null then
        call SelectUnitForPlayerSingle(Hero[p],Player(p))
        call PanCameraToTimedForPlayer(Player(p),GetUnitX(Hero[p]),GetUnitY(Hero[p]),.5)
    endif
endfunction
function StoryMentorThink takes integer t returns nothing
    if StoryMentorsReleased and FoundationAlive(StoryMentor[t]) and FoundationAlive(StoryBoss[t]) and GetUnitCurrentOrder(StoryMentor[t])==0 then
        call IssueTargetOrder(StoryMentor[t],"attack",StoryBoss[t])
    endif
endfunction
function StoryReleaseMentors takes nothing returns nothing
    local integer t=0
    local integer p=0
    set StoryMentorsReleased=true
    if StoryMentorDialog!=null then
        call TimerDialogDisplay(StoryMentorDialog,false)
        call DestroyTimerDialog(StoryMentorDialog)
        set StoryMentorDialog=null
    endif
    call DestroyTimer(StoryMentorClock)
    set StoryMentorClock=null
    loop
        exitwhen t>=4
        if StoryMentor[t]!=null then
            set p=t*3
            loop
                exitwhen p>=t*3+3 or GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING
                set p=p+1
            endloop
            if p<t*3+3 then
                call SetUnitOwner(StoryMentor[t],Player(p),true)
                call UnitRemoveAbility(StoryMentor[t],'Avul')
                call PauseUnit(StoryMentor[t],false)
                call IssuePointOrder(StoryMentor[t],"attack",EnemySpawnX[t*18+15],EnemySpawnY[t*18+15])
                call StorySay(t,StoryMentorName[t]+": Я направляюсь к Забузе. Присоединяйтесь к бою!")
            endif
        endif
        set t=t+1
    endloop
endfunction
function StoryTick takes nothing returns nothing
    local integer t=0
    local integer p=0
    local integer j=0
    local integer alive=0
    local integer first=0
    local integer petSlot=0
    local real dx=0.
    local real dy=0.
    local real x=0.
    local real y=0.
    local unit leader=null
    local unit enemy=null
    local unit target=null
    local boolean cast=false
    call CampaignTick()
    call NextChapterTick()
    call HUDTick()
    loop
        exitwhen t>=4
        if StoryMembers[t]>0 and TimeNow>=6. and StoryPopulateCursor>=64 then
            call StoryMentorThink(t)
            set leader=StoryLeader(t)
            if StoryStage[t]==0 then
                call StoryStartStage(t)
                if StoryHasHuman[t] then
                    call StorySay(t,"Наставник: Дозоры уже в лесу. Выбор героя открыт до выхода или 30-й секунды. -go: начать раньше; -quest: показать цель.")
                endif
            endif
            if not StoryStarted[t] then
                if (not StoryHasHuman[t] and TimeNow>=20.) or TimeNow>=30. then
                    call StoryActivate(t,true)
                    call StorySay(t,"Наставник: Подготовка завершена, выдвигаемся! Напарники идут к дозору. Следуйте за ними; -follow: держаться рядом с вами; -quest: цель.")
                elseif leader!=null and StoryHasHuman[t] then
                    set dx=GetUnitX(leader)-SpawnX[t*3]
                    set dy=GetUnitY(leader)-SpawnY[t*3]
                    if dx*dx+dy*dy>850.*850. then
                        call StoryActivate(t,false)
                        call StorySay(t,"Наставник: Отряд вышел на задание. Напарники прикрывают вас. -go: отправить их к цели; -quest: показать дозор.")
                    endif
                endif
            endif
            if StoryAdvanceAt[t]>0. and TimeNow>=StoryAdvanceAt[t] then
                call StoryStartStage(t)
            endif
            set alive=0
            set first=t*18
            set j=t*18
            loop
                exitwhen j>=t*18+18
                if EnemyPending[j]>0. and TimeNow>=EnemyPending[j] then
                    call StoryEnemyHit(j)
                endif
                if FoundationAlive(StoryEnemy[j]) then
                    if StoryObjectiveEnemy(t,j-t*18) then
                        set alive=alive+1
                        set first=j
                    endif
                    set target=StoryEnemyTarget(t,StoryEnemy[j],leader)
                    if target!=null then
                        set dx=GetUnitX(target)-GetUnitX(StoryEnemy[j])
                        set dy=GetUnitY(target)-GetUnitY(StoryEnemy[j])
                        if dx*dx+dy*dy<850.*850. then
                            if not IsUnitPaused(StoryEnemy[j]) then
                                if TimeNow>=EnemyNext[j] then
                                    call StoryEnemyCast(j,target)
                                    set EnemyFocus[j]=target
                                elseif EnemyPending[j]==0. and (GetUnitCurrentOrder(StoryEnemy[j])==0 or EnemyFocus[j]!=target) then
                                    call IssueTargetOrder(StoryEnemy[j],"attack",target)
                                    set EnemyFocus[j]=target
                                endif
                            endif
                        elseif GetUnitCurrentOrder(StoryEnemy[j])==0 and StoryStage[t]>0 then
                            call IssuePointOrder(StoryEnemy[j],"move",EnemySpawnX[j],EnemySpawnY[j])
                        endif
                    endif
                elseif StoryEnemy[j]!=null then
                    call StoryDrop(j)
                endif
                set j=j+1
            endloop
            if StoryStage[t]==1 and alive<=7 then
                set alive=0
            endif
            set Dummy[t]=StoryEnemy[first]
            if StoryStage[t]>0 and StoryStage[t]<5 and alive==0 and StoryAdvanceAt[t]==0. then
                call StoryReward(t,150+StoryStage[t]*100,0)
                call StorySay(t,"Наставник: Отличная работа! Награда всему отряду: золото. Можно отдохнуть и пополнить снаряжение.")
                if StoryStage[t]==4 then
                    set StoryStage[t]=5
                    call StorySay(t,"Тадзуна: Мост спасён! Спасибо вам, шиноби Конохи. |n"+StoryGoal(t))
                else
                    set StoryAdvanceAt[t]=TimeNow+8.
                endif
            endif
            set p=t*3
            loop
                exitwhen p>=t*3+3
                if Hero[p]!=null and not CampaignPermanentDead[p] then
                    if not FoundationAlive(Hero[p]) and not CampaignPermanentDead[p] then
                        if StoryRevive[p]==0. then
                            set StoryRevive[p]=TimeNow+20.
                            call DisplayTimedTextToPlayer(Player(p),0.,0.,10.,"Наставник: Мы тебя прикроем. Возвращение в лагерь через 20 секунд.")
                        elseif TimeNow>=StoryRevive[p] then
                            call ReviveHero(Hero[p],SpawnX[p],SpawnY[p],true)
                            set StoryRevive[p]=0.
                            call SetUnitState(Hero[p],UNIT_STATE_MANA,GetUnitState(Hero[p],UNIT_STATE_MAX_MANA))
                        endif
                    else
                        set StoryRevive[p]=0.
                        set dx=GetUnitX(Hero[p])-SpawnX[p]
                        set dy=GetUnitY(Hero[p])-SpawnY[p]
                        if CampaignStage!=9 and CampaignStage!=11 and StoryStage[t]<9 and not CampaignTransition and dx*dx+dy*dy<700.*700. then
                            call SetWidgetLife(Hero[p],RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE),GetWidgetLife(Hero[p])+15.))
                            call SetUnitState(Hero[p],UNIT_STATE_MANA,RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_MANA),GetUnitState(Hero[p],UNIT_STATE_MANA)+12.))
                        endif
                        if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and TimeNow>=BotNextCast[p] and JumpUnit[p]==null and JumpQueued[p]==null and StoryStage[t]!=6 and StoryStage[t]!=8 and not IsUnitPaused(Hero[p]) and not CampaignTransition then
                            call SkillsLearnBot(p)
                            if StoryStage[t]>=9 then
                                set enemy=CampaignNearest(p)
                            elseif StoryStage[t]==7 then
                                set enemy=ExamNearest(p)
                            else
                                set enemy=StoryNearest(t,Hero[p])
                            endif
                            set cast=CommonLogBot(p,enemy)
                            if not cast then
                                set cast=StoryStatLootBot(p,enemy)
                            endif
                            if not cast then
                                set cast=StoryLootBot(p,enemy)
                            endif
                            if enemy!=null and not cast then
                                set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
                                set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
                                set Dummy[t]=enemy
                                if dx*dx+dy*dy<750.*750. and not (CampaignStage==15 and p==CampaignSasukePlayer) and not StoryRetreat[t] and not (StoryStage[t]==7 and ExamTowerOpen and ExamPair(t)) then
                                    set cast=SkillsBot(p)
                                endif
                            endif
                            if not cast and TimeNow>=StoryBotOrderAt[p] then
                                set StoryBotOrderAt[p]=TimeNow+2.
                                set petSlot=0
                                loop
                                    exitwhen petSlot>=3
                                    if FoundationAlive(Companion[p*3+petSlot]) then
                                        if enemy!=null then
                                            set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
                                            set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
                                        else
                                            set dx=9999.
                                        endif
                                        if not StoryRetreat[t] and dx*dx+dy*dy<900.*900. then
                                            call IssueTargetOrder(Companion[p*3+petSlot],"attack",enemy)
                                        else
                                            call IssueTargetOrder(Companion[p*3+petSlot],"follow",Hero[p])
                                        endif
                                    endif
                                    set petSlot=petSlot+1
                                endloop
                                if StoryStage[t]>=9 then
                                    call CampaignBot(p,enemy)
                                elseif StoryStage[t]==7 then
                                    call ExamBot(p,enemy)
                                elseif StoryRetreat[t] or GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2 then
                                    call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
                                elseif not StoryStarted[t] or StoryStage[t]==5 then
                                    call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
                                elseif enemy!=null then
                                    set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
                                    set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
                                    if StoryMarch[t] or dx*dx+dy*dy<800.*800. then
                                        call IssueTargetOrder(Hero[p],"attack",enemy)
                                    elseif leader!=null and leader!=Hero[p] then
                                        set dx=GetUnitX(Hero[p])-GetUnitX(leader)
                                        set dy=GetUnitY(Hero[p])-GetUnitY(leader)
                                        if dx*dx+dy*dy>300.*300. then
                                            call IssuePointOrder(Hero[p],"move",GetUnitX(leader)+(ModuloInteger(p,3)-1)*80.,GetUnitY(leader)-80.)
                                        endif
                                    endif
                                endif
                            endif
                        endif
                    endif
                endif
                set p=p+1
            endloop
        endif
        set t=t+1
    endloop
    set leader=null
    set target=null
    set enemy=null
endfunction
function StoryInit takes nothing returns nothing
    local integer t=0
    local integer p=0
    local integer n=0
    local unit npc=null
    local quest journal=CreateQuest()
    call QuestSetTitle(journal,"Путь шиноби — сюжет и задания")
    call QuestSetDescription(journal,"Четыре отряда проходят лесные задания независимо. Задание и метка: -quest. Команды напарникам: -go, -follow, -retreat. Выберите героя до выхода на миссию. После Хаку и Забузы: вопросы Ибики, свитки в Лесу смерти, предварительные поединки, поиск Джирайи в бочках и турнир. Далее — вторжение в деревню, Акацуки, Пятёрка Звука и погоня за Саске. Сюжетные роли привязаны к героям; игрок за Саске позже меняет сторону.")
    call QuestSetRequired(journal,true)
    call QuestSetDiscovered(journal,true)
    loop
        exitwhen t>=4
        set p=t*3
        loop
            exitwhen p>=t*3+3
            if GetPlayerSlotState(Player(p))==PLAYER_SLOT_STATE_PLAYING then
                set StoryMembers[t]=StoryMembers[t]+1
                if GetPlayerController(Player(p))!=MAP_CONTROL_COMPUTER then
                    set StoryHasHuman[t]=true
                endif
            endif
            set p=p+1
        endloop
        if StoryMembers[t]>0 then
            set npc=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),StoryMentorType[t],SpawnX[t*3]+180.,SpawnY[t*3]+180.,0.)
            set StoryMentor[t]=npc
            call PauseUnit(npc,true)
            call StorySay(t,"Наставник: Наша миссия — защитить строителя моста в Стране Волн. Дорогу перекрыли шиноби Тумана. Подготовьтесь, затем отправляемся вместе. |n"+StoryGoal(t))
        endif
        set t=t+1
    endloop
    set StoryPopulateClock=CreateTimer()
    call TimerStart(StoryPopulateClock,.05,true,function StoryPopulate)
    set StoryMentorClock=CreateTimer()
    call TimerStart(StoryMentorClock,330.,false,function StoryReleaseMentors)
    // Timer dialogs and the board are created by HUDTick after game UI is ready.
    set npc=null
    set journal=null
endfunction
