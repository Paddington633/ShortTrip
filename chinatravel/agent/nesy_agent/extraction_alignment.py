"""Source coverage and bounded, item-wise extraction repair; no search logic."""
import ast
import difflib
import json
import re
from copy import deepcopy
from .translation_contract import TranslationValidationError
from .constraint_compiler import comparison,_catalog,_validate_extraction_items

CATEGORY_ALIASES={
 '博物馆':'博物馆/纪念馆','历史景点':'历史古迹','历史人文景点':'历史古迹',
 '历史人文':'历史古迹','历史':'历史古迹','自然景点':'自然风光','自然风光':'自然风光',
 '大学校园':'大学校园','大学里':'大学校园','大学':'大学校园'}

def literal(values):return '{'+', '.join(repr(v) for v in sorted(values))+'}'
def set_code(field,values,any_of=False):
    if any_of and len(values)>1:
        return '('+' or '.join(literal({v})+'<='+field for v in sorted(values))+')'
    return literal(values)+'<='+field

def aliases(names):
    result={}
    for name in sorted(names):
        result.setdefault(name,set()).add(name)
        for suffix in ('风景名胜区','风景区','景区','游船'):
            if name.endswith(suffix) and len(name)>len(suffix)+1:
                if suffix=='游船' and not name[:-len(suffix)].endswith('号'):continue
                result.setdefault(name[:-len(suffix)],set()).add(name)
        match=re.fullmatch(r'(.+?)[(（][^()（）]*校区[)）]',name)
        if match:result.setdefault(match[1],set()).add(name)
    return result

def resolve_name(value,field,catalog):
    mapping=aliases(catalog[field]);options=mapping.get(value)
    if options:
        if len(options)==1:return set(options),False
        # Multiple campuses of an explicitly named university are alternatives.
        if all(re.fullmatch(re.escape(value)+r'[(（][^()（）]*校区[)）]',n) for n in options):
            return set(options),True
    candidates=sorted(options or {n for n in catalog[field] if value in n})
    if not candidates:candidates=difflib.get_close_matches(value,sorted(catalog[field]),n=5,cutoff=.35)
    raise TranslationValidationError(f'Ambiguous or unresolved {field} {value!r}; canonical candidates: {candidates[:5]}; do not select arbitrarily')

def positive(text,start):
    prefix=re.split('[，,。;；\n]',text[:start])[-1]
    return not re.search(r'不去|不坐|不用|不乘|不要|不想|无需|不需要|尽量|尽可能|如果有时间|avoid|if possible',prefix[-25:],re.I)

def coverage(query,catalog):
    text=query['nature_language'];entries=[];occupied=[]
    def add(code,source,field,values=None,any_of=False):
        if not any(e['code']==code for e in entries):
            entries.append(dict(code=code,source=source,field=field,values=sorted(values) if values else None,any_of=any_of))
    for field in ('attraction_names','restaurant_names','hotel_names'):
        mapping=aliases(catalog[field]);mentions=[]
        for alias,options in mapping.items():
            if len(alias)<2:continue
            for match in re.finditer(re.escape(alias),text):
                if positive(text,match.start()):mentions.append((match.start(),match.end(),alias))
        selected=[]
        for start,end,alias in sorted(mentions,key=lambda x:-(x[1]-x[0])):
            if any(start<e and end>s for s,e,_ in selected):continue
            selected.append((start,end,alias))
        for start,end,alias in sorted(selected):
            try:values,any_of=resolve_name(alias,field,catalog)
            except TranslationValidationError as exc:
                entries.append(dict(code=None,source=alias,field=field,values=None,any_of=False,pending=str(exc)))
                occupied.append((start,end));continue
            add(set_code(field,values,any_of),alias,field,values,any_of);occupied.append((start,end))
    masked=list(text)
    for start,end in occupied:masked[start:end]=' '* (end-start)
    remaining=''.join(masked)
    used=[]
    for alias,canonical in sorted(CATEGORY_ALIASES.items(),key=lambda x:-len(x[0])):
        for match in re.finditer(re.escape(alias),remaining):
            if any(match.start()<e and match.end()>s for s,e in used):continue
            if positive(text,match.start()) and canonical in catalog['spot_type']:
                add(set_code('spot_type',{canonical}),alias,'spot_type',{canonical});used.append(match.span())
    for cuisine in sorted(catalog['food_type'],key=lambda v:-len(v)):
        if len(cuisine)>1:
            match=re.search(re.escape(cuisine),remaining)
            if match and positive(text,match.start()):add(set_code('food_type',{cuisine}),cuisine,'food_type',{cuisine})
    budget=re.search(r'(?:预算(?:在|为|是|约|大概|大约)?|budget\s*(?:of|is)?\s*)\s*(\d+(?:\.\d+)?)\s*([万千]?)',text,re.I)
    if budget:
        amount=float(budget[1])*{'':1,'万':10000,'千':1000}[budget[2]]
        if amount.is_integer():amount=int(amount)
        add('cost<='+repr(amount),budget[0],'cost')
    for pattern,field,mode in [(r'火车|高铁|动车|\btrain\b','intercity_transport','train'),
                               (r'飞机|航班|\bflight\b','intercity_transport','airplane'),
                               (r'地铁|\bmetro\b|\bsubway\b','transport_type','metro')]:
        match=re.search(pattern,text,re.I)
        if match and positive(text,match.start()):
            operator='==' if field=='intercity_transport' else '<='
            add(field+operator+literal({mode}),match[0],field,{mode})
    prefix=re.search(r'高铁\s*[(（]?\s*(G)(?![A-Za-z])|(?<![A-Za-z])(G)\s*(?:字头|字首)',text,re.I)
    if prefix:add("train_type=={'G'}",prefix[0],'train_type',{'G'})
    deadline=re.search(r'(?:不超过|不晚于|最晚|\bby\s+|\bbefore\s+)\s*(\d{1,2})(?:[:：](\d{2})|点(?:钟)?)',text,re.I)
    if deadline and re.search(r'返|回来|上火车|上车|return',text,re.I):
        hour=int(deadline[1]);minute=int(deadline[2] or 0)
        if hour>23 or minute>59:raise TranslationValidationError('Invalid explicit return deadline')
        add("return_start_time<="+repr(f'{hour:02d}:{minute:02d}'),deadline[0],'return_start_time')
    return entries

def facts_in(code):
    fact=comparison(code)
    if fact:return [fact]
    try:tree=ast.parse(code,mode='eval').body
    except SyntaxError:return []
    if isinstance(tree,ast.BoolOp) and isinstance(tree.op,ast.Or):
        facts=[comparison(ast.unparse(node)) for node in tree.values]
        if all(facts):return facts
    return []

def ast_key(code):
    try:return ast.dump(ast.parse(code,mode='eval'))
    except (SyntaxError,TypeError):return None

class ExtractionState:
    def __init__(self,query):
        self.query=deepcopy(query);self.catalog=_catalog(query['target_city'])
        self.checklist=coverage(query,self.catalog);self.locked={};self.errors=[]
        self.derived={}
        for field,value in [('days',query.get('days')),('people_number',query.get('people_number')),
                            ('tickets',query.get('people_number')),
                            ('taxi_cars',(query['people_number']+3)//4 if query.get('people_number') else None)]:
            if value is not None:self.derived[field]=value
        for field,value in self.derived.items():
            code=field+'=='+str(value)
            self.locked[code]=dict(constraint=code,source='input metadata / passenger-count derivation',derived=True)

    def instructions(self):
        return ('\nSource coverage checklist (all explicit items must remain; alternatives use OR):\n'
                +json.dumps(self.checklist,ensure_ascii=False)
                +'\nAlready validated constraints (locked; do not remove or alter):\n'
                +json.dumps(list(self.locked.values()),ensure_ascii=False)
                +'\nReturn hard_logic and hard_logic_evidence for missing/incorrect items only, or all items. No invented requirements.\n')

    def normalize(self,code,source):
        fact=comparison(code)
        if not fact:return [(code,source)]
        field,op,value,shape=fact
        if field in self.derived:
            if not isinstance(op,ast.Eq) or value!=self.derived[field]:
                raise TranslationValidationError(f'{field} must match authoritative input {self.derived[field]}')
            return [(field+'=='+str(value),None)]
        if shape=='set' and field in ('attraction_names','restaurant_names','hotel_names','spot_type','food_type','hotel_feature') and isinstance(value,set):
            result=[]
            for item in sorted(value):
                if field.endswith('_names'):
                    family=next((e for e in self.checklist if e['field']==field and e['any_of'] and (item==e['source'] or item in e['values'])),None)
                    values,any_of=(set(family['values']),True) if family else resolve_name(item,field,self.catalog)
                else:values={CATEGORY_ALIASES.get(item,item) if field=='spot_type' else item};any_of=False
                canonical=set_code(field,values,any_of)
                entry=next((e for e in self.checklist if e['code']==canonical),None)
                result.append((canonical,entry['source'] if entry else source))
            return result
        entry=next((e for e in self.checklist if ast_key(e['code'])==ast_key(code) and ast_key(code)),None)
        return [(entry['code'],entry['source'])] if entry else [(code,source)]

    def covered(self,entry):
        if entry['code'] is None:return False
        if entry['any_of']:
            return any(len(facts_in(c))>1 and all(f[0]==entry['field'] for f in facts_in(c))
                       and set(entry['values'])<={v for f in facts_in(c) for v in f[2]} for c in self.locked)
        expected=comparison(entry['code'])
        for code in self.locked:
            actual=comparison(code)
            if not actual:continue
            if expected[0]!=actual[0] or type(expected[1])!=type(actual[1]) or expected[3]!=actual[3]:continue
            if isinstance(expected[2],set) and isinstance(actual[2],set):
                if expected[2]<=actual[2]:return True
            elif expected[2]==actual[2]:return True
        return False

    def accept(self,parsed):
        if not isinstance(parsed,dict) or not isinstance(parsed.get('hard_logic'),list):
            raise TranslationValidationError('Expected extraction JSON object with hard_logic list')
        quotes={e.get('constraint'):e.get('source') for e in parsed.get('hard_logic_evidence',[]) if isinstance(e,dict)}
        errors=[]
        for code in parsed['hard_logic']:
            try:
                if not isinstance(code,str) or not code.strip():raise TranslationValidationError('Constraint must be a nonempty string')
                for normalized,source in self.normalize(code,quotes.get(code)):
                    if normalized in self.locked:continue
                    # Recognize an explicitly supplied OR form from the checklist.
                    entry=next((e for e in self.checklist if ast_key(e['code'])==ast_key(normalized) and ast_key(normalized)),None)
                    source=entry['source'] if entry else source
                    evidence=dict(constraint=normalized,source=source)
                    if entry and entry['any_of']:
                        # Every option came from the same explicit DB campus family.
                        self.locked[normalized]=evidence
                    else:
                        _validate_extraction_items(self.query,dict(hard_logic=[normalized],hard_logic_evidence=[evidence]))
                        self.locked[normalized]=evidence
            except (ValueError,TypeError,KeyError) as exc:errors.append(f'{code}: {exc}')
        missing=[e for e in self.checklist if not self.covered(e)]
        if missing:errors.append('Missing explicit requirements: '+json.dumps(missing,ensure_ascii=False))
        self.errors=errors
        if errors:raise TranslationValidationError('\n'.join(errors))
        result=dict(parsed);result['hard_logic']=list(self.locked)
        result['hard_logic_evidence']=list(self.locked.values());result['source_coverage']=self.checklist
        return result

def grounded_extraction(query,parsed):
    try:return ExtractionState(query).accept(parsed)
    except TranslationValidationError as exc:
        raise TranslationValidationError('Translation extraction validation: '+str(exc)) from exc

def extract_with_repair(query,llm,prompt):
    state=ExtractionState(query)
    error=None
    for attempt in range(3):
        content=prompt+state.instructions()
        if error:content+='\nRepair only the following errors/missing items; validated constraints remain locked:\n'+str(error)
        response=llm([{'role':'user','content':content}],one_line=False,json_mode=True)
        try:
            parsed=json.loads(response)
            if not isinstance(parsed,dict):raise TranslationValidationError('Extraction must be a JSON object')
            for key in ('uid','days','people_number','start_city','target_city'):
                if key in query and key in parsed and query[key]!=parsed[key]:
                    raise TranslationValidationError('Extraction changed input field '+key)
            result=state.accept(parsed)
            # Preserve the input and only update translation-owned fields.
            for key in ('hard_logic','hard_logic_evidence','source_coverage'):query[key]=result[key]
            query['extraction_repair_count']=attempt
            return query
        except (ValueError,TypeError,KeyError) as exc:error=exc
    raise TranslationValidationError('Translation stage 1 failed after 3 attempts: '+str(error))
