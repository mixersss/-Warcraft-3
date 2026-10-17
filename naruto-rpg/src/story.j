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
    return "Глава «Страна Волн» завершена! Следующая глава — экзамен со свитками — пока не подключена."
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
        if n<14 and ModuloInteger(n,2)==1 then
            set raw='re02'
            set EnemyKind[j]=2
        elseif n==14 then
            set raw='re03'
            set EnemyKind[j]=3
        elseif n==15 then
            set raw='re04'
            set EnemyKind[j]=4
        endif
        set u=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),raw,EnemySpawnX[j],EnemySpawnY[j],180.)
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
function StoryEnemyTarget takes integer t, unit enemy, unit leader returns unit
    local real dx=0.
    local real dy=0.
    local real distance=999999999.
    if leader!=null then
        set dx=GetUnitX(leader)-GetUnitX(enemy)
        set dy=GetUnitY(leader)-GetUnitY(enemy)
        set distance=dx*dx+dy*dy
    endif
    if StoryMentorsReleased and FoundationAlive(StoryMentor[t]) then
        set dx=GetUnitX(StoryMentor[t])-GetUnitX(enemy)
        set dy=GetUnitY(StoryMentor[t])-GetUnitY(enemy)
        if dx*dx+dy*dy<distance then
            return StoryMentor[t]
        endif
    endif
    return leader
endfunction
function StoryEnemyCast takes integer j, unit target returns nothing
    local integer t=(j-ModuloInteger(j,18))/18
    local integer stage=EnemyKind[j]
    local unit u=StoryEnemy[j]
    local unit clone=null
    local integer n=1
    set EnemyX[j]=GetUnitX(target)
    set EnemyY[j]=GetUnitY(target)
    set EnemyPending[j]=TimeNow+1.5
    set EnemyMark[j]=AddSpecialEffect("Abilities\\Spells\\Human\\Blizzard\\BlizzardTarget.mdl",EnemyX[j],EnemyY[j])
    call IssueImmediateOrder(u,"stop")
    call SetUnitFacing(u,bj_RADTODEG*Atan2(EnemyY[j]-GetUnitY(u),EnemyX[j]-GetUnitX(u)))
    if stage==3 then
        // Haku has no Spell sequence: use the actual second Attack sequence.
        call SetUnitAnimationByIndex(u,2)
    elseif stage==4 then
        call SetUnitAnimationByIndex(u,5)
    elseif stage==1 then
        call SetUnitAnimationByIndex(u,5)
    else
        call SetUnitAnimationByIndex(u,4)
    endif
    set EnemyNext[j]=TimeNow+9.
    if stage>=3 and GetWidgetLife(u)<GetUnitState(u,UNIT_STATE_MAX_LIFE)*.5 then
        set EnemyNext[j]=TimeNow+5.5
        if not EnemyPhase[j] then
            set EnemyPhase[j]=true
            if stage==4 and ModuloInteger(j,18)==15 then
                loop
                    exitwhen n>=3
                    set clone=CreateUnit(Player(PLAYER_NEUTRAL_AGGRESSIVE),'re05',GetUnitX(u)+n*100.,GetUnitY(u)+100.,180.)
                    call SetUnitVertexColor(clone,100,170,255,155)
                    call SetUnitCreepGuard(clone,false)
                    call RemoveGuardPosition(clone)
                    set StoryEnemy[t*18+15+n]=clone
                    set EnemySpawnX[t*18+15+n]=GetUnitX(clone)
                    set EnemySpawnY[t*18+15+n]=GetUnitY(clone)
                    set EnemyPrisonAt[t*18+15+n]=TimeNow+99999.
                    set EnemyKind[t*18+15+n]=4
                    set EnemyNext[t*18+15+n]=TimeNow+99999.
                    set EnemyLootRolled[t*18+15+n]=true
                    call IssueTargetOrder(clone,"attack",target)
                    set n=n+1
                endloop
                call StorySay(t,"Забуза: Техника водяных клонов! |nНаставник: Клоны хрупкие — разберите их вместе, затем сосредоточьтесь на настоящем Забузе!")
            endif
            call StorySay(t,"Наставник: Противник усиливает натиск! Не стойте рядом друг с другом и берегите чакру.")
        endif
    endif
    set clone=null
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
    local integer chance=20
    local integer choice=0
    if EnemyLootRolled[j] or StoryEnemy[j]==null then
        return
    endif
    set EnemyLootRolled[j]=true
    if EnemyKind[j]==3 then
        set chance=60
    elseif EnemyKind[j]==4 then
        set chance=100
    endif
    if GetRandomInt(1,100)<=chance then
        if GetRandomInt(1,100)<=5 then
            set choice=1
        else
            set choice=GetRandomInt(0,5)
            if choice>=1 then
                set choice=choice+1
            endif
        endif
        set StoryLoot[j]=CreateItem(StoryLootType[choice],GetUnitX(StoryEnemy[j]),GetUnitY(StoryEnemy[j]))
    endif
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
function StoryBuy takes integer p returns nothing
    local integer t=StoryTeam(p)
    local integer slot=0
    local integer choice=0
    local integer role=HeroRole[p]
    local boolean full=true
    if TimeNow<StoryBuyAt[p] or GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)<120 then
        return
    endif
    loop
        exitwhen slot>=6
        if UnitItemInSlot(Hero[p],slot)==null then
            set full=false
        endif
        set slot=slot+1
    endloop
    if full then
        return
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
    if GetPlayerState(Player(p),PLAYER_STATE_RESOURCE_GOLD)>=StoryPrice[choice] then
        call IssueNeutralTargetOrder(Player(p),StoryShop[t],"neutralinteract",Hero[p])
        call IssueNeutralImmediateOrderById(Player(p),StoryShop[t],StoryItem[choice])
        set StoryBuyAt[p]=TimeNow+4.
    endif
endfunction
function StoryOnBuy takes nothing returns nothing
    local unit buyer=GetBuyingUnit()
    local integer p=GetPlayerId(GetOwningPlayer(buyer))
    if p<12 and buyer==Hero[p] then
        set StoryBought[p]=StoryBought[p]+1
    endif
    set buyer=null
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
function StoryCommand takes integer p, string msg returns nothing
    local integer t=StoryTeam(p)
    local integer n=0
    local unit goal=null
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
        if StoryStage[t]>0 and StoryStage[t]<5 then
            set goal=StoryNearest(t,Hero[p])
            if goal!=null then
                call PingMinimapEx(GetUnitX(goal),GetUnitY(goal),5.,255,210,50,false)
            endif
            set goal=null
        endif
    elseif msg=="-shop" then
        call SelectUnitForPlayerSingle(StoryShop[t],Player(p))
        call PanCameraToTimedForPlayer(Player(p),GetUnitX(StoryShop[t]),GetUnitY(StoryShop[t]),1.)
        call DisplayTimedTextToPlayer(Player(p),0.,0.,10.,"Снабжение возле Наставник: подведите своего героя и купите предмет кнопкой магазина. -camera: вернуться к герою.")
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
                            if EnemyKind[j]==4 and ModuloInteger(j,18)==15 and TimeNow>=EnemyPrisonAt[j] and dx*dx+dy*dy<=700.*700. and GetUnitState(StoryEnemy[j],UNIT_STATE_MANA)>=80. then
                                if IssueTargetOrder(StoryEnemy[j],"thunderbolt",target) then
                                    set EnemyPrisonAt[j]=TimeNow+12.
                                    set EnemyNext[j]=RMaxBJ(EnemyNext[j],TimeNow+2.)
                                endif
                            elseif EnemyKind[j]==4 and ModuloInteger(j,18)==15 and TimeNow>=EnemyBlinkAt[j] and dx*dx+dy*dy>500.*500. and GetUnitState(StoryEnemy[j],UNIT_STATE_MANA)>=30. then
                                if IssuePointOrder(StoryEnemy[j],"blink",GetUnitX(target),GetUnitY(target)) then
                                    set EnemyBlinkAt[j]=TimeNow+10.
                                    set EnemyNext[j]=RMaxBJ(EnemyNext[j],TimeNow+1.)
                                endif
                            elseif TimeNow>=EnemyNext[j] then
                                call StoryEnemyCast(j,target)
                            elseif EnemyPending[j]==0. and GetUnitCurrentOrder(StoryEnemy[j])==0 then
                                call IssueTargetOrder(StoryEnemy[j],"attack",target)
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
                if Hero[p]!=null then
                    if not FoundationAlive(Hero[p]) then
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
                        if dx*dx+dy*dy<700.*700. then
                            call SetWidgetLife(Hero[p],RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE),GetWidgetLife(Hero[p])+15.))
                            call SetUnitState(Hero[p],UNIT_STATE_MANA,RMinBJ(GetUnitState(Hero[p],UNIT_STATE_MAX_MANA),GetUnitState(Hero[p],UNIT_STATE_MANA)+12.))
                        endif
                        if GetPlayerController(Player(p))==MAP_CONTROL_COMPUTER and TimeNow>=BotNextCast[p] and JumpUnit[p]==null and JumpQueued[p]==null then
                            call SkillsLearnBot(p)
                            set enemy=StoryNearest(t,Hero[p])
                            set cast=StoryLootBot(p,enemy)
                            if enemy!=null and not cast then
                                set dx=GetUnitX(Hero[p])-GetUnitX(enemy)
                                set dy=GetUnitY(Hero[p])-GetUnitY(enemy)
                                set Dummy[t]=enemy
                                if dx*dx+dy*dy<750.*750. and not StoryRetreat[t] then
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
                                if StoryRetreat[t] or GetWidgetLife(Hero[p])<GetUnitState(Hero[p],UNIT_STATE_MAX_LIFE)*.2 then
                                    call IssuePointOrder(Hero[p],"move",SpawnX[p],SpawnY[p])
                                elseif not StoryStarted[t] or StoryStage[t]>=5 then
                                    set x=GetUnitX(StoryShop[t])
                                    set y=GetUnitY(StoryShop[t])
                                    set dx=GetUnitX(Hero[p])-x
                                    set dy=GetUnitY(Hero[p])-y
                                    if dx*dx+dy*dy<200.*200. then
                                        call StoryBuy(p)
                                    else
                                        call IssuePointOrder(Hero[p],"move",x,y)
                                    endif
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
    local trigger sell=CreateTrigger()
    local unit npc=null
    local quest journal=CreateQuest()
    call QuestSetTitle(journal,"Глава I. Страна Волн")
    call QuestSetDescription(journal,"Четыре отряда проходят лесные задания независимо. Задание и метка: -quest. Команды напарникам: -go, -follow, -retreat. Выберите героя до выхода на миссию. Победите дозоры, Хаку и Забузу; помогайте союзникам и покупайте снаряжение.")
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
            set StoryShop[t]=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'rqsh',SpawnX[t*3]+280.,SpawnY[t*3]-180.,0.)
            call TriggerRegisterUnitEvent(sell,StoryShop[t],EVENT_UNIT_SELL_ITEM)
            call StorySay(t,"Наставник: Наша миссия — защитить строителя моста в Стране Волн. Дорогу перекрыли шиноби Тумана. Подготовьтесь, затем отправляемся вместе. |n"+StoryGoal(t))
        endif
        set t=t+1
    endloop
    set StoryPopulateClock=CreateTimer()
    call TimerStart(StoryPopulateClock,.05,true,function StoryPopulate)
    set StoryMentorClock=CreateTimer()
    set StoryMentorDialog=CreateTimerDialog(StoryMentorClock)
    call TimerDialogSetTitle(StoryMentorDialog,"До выхода наставников")
    call TimerStart(StoryMentorClock,330.,false,function StoryReleaseMentors)
    call TimerDialogDisplay(StoryMentorDialog,true)
    call TriggerAddAction(sell,function StoryOnBuy)
    set npc=null
    set journal=null
    set sell=null
endfunction
