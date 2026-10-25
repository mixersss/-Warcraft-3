// Full user tracks in a fixed order, one reused timer for the entire playlist.
function FFMusicNext takes nothing returns nothing
    set FFMusicIndex=ModuloInteger(FFMusicIndex+1,8)
    call ExecuteFunc("FFMusicPlay")
endfunction
function FFMusicPlay takes nothing returns nothing
    call StopMusic(false)
    call PlayMusic(FFMusicPath[FFMusicIndex])
    call TimerStart(FFMusicTimer,FFMusicSeconds[FFMusicIndex],false,function FFMusicNext)
endfunction
function FFMusicInit takes nothing returns nothing
    if FFMusicTimer!=null then
        return
    endif
    // PLAYLIST_DATA
    set FFMusicTimer=CreateTimer()
    call FFMusicPlay()
endfunction
