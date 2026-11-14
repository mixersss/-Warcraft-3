"""Static Lua function/call inventory; does not execute source or expose function bodies."""
import bisect,hashlib,re

WORD=re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
NUMBER=re.compile(r'0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?')
KEYWORDS={'if','then','elseif','else','end','for','while','repeat','until','do','function','return','local','and','or','not','in'}
LONG_OPEN=re.compile(r'\[(=*)\[')

def tokens(source):
    out=[];i=0
    while i<len(source):
        if source[i].isspace():i+=1;continue
        start=i;comment=source.startswith('--',i)
        if comment:i+=2
        long=LONG_OPEN.match(source,i)
        if long:
            close=']'+long[1]+']';end=source.find(close,i+len(long[0]))
            if end<0:raise ValueError('Unterminated Lua long string/comment')
            finish=end+len(close)
            if not comment:out.append(('string',source[i+len(long[0]):end],start,finish))
            i=finish;continue
        if comment:
            end=source.find('\n',i);i=len(source) if end<0 else end;continue
        if source[i] in '\"\'':
            quote=source[i];i+=1;content=[]
            while i<len(source):
                if source[i]=='\\' and i+1<len(source):content.append(source[i:i+2]);i+=2;continue
                if source[i]==quote:break
                content.append(source[i]);i+=1
            if i==len(source):raise ValueError('Unterminated Lua quoted string')
            i+=1;out.append(('string',''.join(content),start,i));continue
        match=WORD.match(source,i) or NUMBER.match(source,i)
        if match:
            value=match[0];i=match.end();out.append(('identifier' if value[0].isalpha() or value[0]=='_' else 'number',value,start,i));continue
        op=next((op for op in ('...','==','~=','<=','>=','..') if source.startswith(op,i)),source[i])
        i+=len(op);out.append(('symbol',op,start,i))
    return out

def functions(source):
    stream=tokens(source);stack=[];result=[];errors=[]
    linebreaks=[i for i,c in enumerate(source) if c=='\n']
    for index,token in enumerate(stream):
        kind,value,start,end=token
        if kind!='identifier':continue
        if value=='function':
            j=index+1;parts=[]
            while j<len(stream) and stream[j][1]!='(':
                if stream[j][0]=='identifier' or stream[j][1] in ('.',':'):parts.append(stream[j][1])
                else:break
                j+=1
            stack.append({'kind':'function','name':''.join(parts) or None,'start':start,'token':index})
        elif value in ('if','for','while','repeat'):
            stack.append({'kind':value,'pending_do':value in ('for','while')})
        elif value=='do':
            if stack and stack[-1].get('pending_do'):stack[-1]['pending_do']=False
            else:stack.append({'kind':'do'})
        elif value in ('end','until'):
            if not stack:errors.append({'line':bisect.bisect_left(linebreaks,start)+1,'kind':'unmatched_'+value});continue
            block=stack.pop()
            if value=='until' and block['kind']!='repeat':errors.append({'line':bisect.bisect_left(linebreaks,start)+1,'kind':'until_mismatch'})
            if block['kind']=='function' and block['name']:
                body=stream[block['token']:index+1]
                signature_end=next((i for i,t in enumerate(body) if t[1]==')'),0)
                calls=sorted({t[1] for i,t in enumerate(body[:-1]) if i>signature_end and t[0]=='identifier'
                              and t[1] not in KEYWORDS and body[i+1][1]=='('})
                result.append({'name':block['name'],'line':bisect.bisect_left(linebreaks,block['start'])+1,
                               'end_line':bisect.bisect_left(linebreaks,end)+1,'calls':calls,
                               'sha256':hashlib.sha256(source[block['start']:end].encode()).hexdigest(),
                               '_tokens':body,'_body':source[block['start']:end]})
    if stack:errors.append({'kind':'unclosed_blocks','count':len(stack)})
    return sorted(result,key=lambda r:r['line']),errors

def literal_calls(stream,name):
    """Only flat literal arguments or variable names; complex calls stay unknown."""
    result=[]
    for i,t in enumerate(stream[:-1]):
        if t[0]!='identifier' or t[1]!=name or stream[i+1][1]!='(':continue
        depth=0;args=[];part=[]
        for token in stream[i+2:]:
            if token[1]=='(' and token[0]!='string':depth+=1
            if token[1]==')' and token[0]!='string':
                if not depth:
                    if part:args.append(part)
                    break
                depth-=1
            if token[1]==',' and not depth and token[0]!='string':args.append(part);part=[]
            else:part.append(token)
        values=[]
        for part in args:
            if len(part)==1 and part[0][0] in ('string','number'):
                values.append(part[0][1] if part[0][0]=='string' else float(part[0][1]) if '.' in part[0][1] else int(part[0][1],0) if part[0][1].startswith(('0x','0X')) else int(part[0][1]))
            elif len(part)==1 and part[0][0]=='identifier':values.append({'variable':part[0][1]})
            elif len(part)==2 and part[0][1]=='-' and part[1][0]=='number':values.append(-int(part[1][1]))
            else:values.append({'dynamic':True})
        result.append(values)
    return result
