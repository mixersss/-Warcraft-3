-- Native UI surrogate: check values, deadlines and balanced item-handle releases.
function IsUnitPaused(u)return u and u.paused or false end
HUDItemsAcquired=0;HUDItemsReleased=0
function CreateMultiboard()return {cells={}}end
function MultiboardSetTitleText(b,s)b.title=s end
function MultiboardSetRowCount(b,n)b.rows=n end
function MultiboardSetColumnCount(b,n)b.cols=n end
function MultiboardSetItemsStyle()end
function MultiboardSetItemsWidth()end
function MultiboardDisplay(b,v)b.visible=v end
function MultiboardMinimize(b,v)b.minimized=v end
function MultiboardGetItem(b,r,c)assert(r>=0 and r<b.rows and c>=0 and c<b.cols);HUDItemsAcquired=HUDItemsAcquired+1;return {board=b,row=r,col=c}end
function MultiboardSetItemValue(i,v)i.board.cells[i.row*3+i.col]=v end
function MultiboardReleaseItem(i)assert(not i.released);i.released=true;HUDItemsReleased=HUDItemsReleased+1 end
function I2S(n)return tostring(math.floor(n))end
