# import List from typing
from cmd import IDENTCHARS
from typing import List
from tinycss2.ast import Node
from tinycss2.ast import QualifiedRule
from tinycss2.ast import WhitespaceToken,IdentToken,LiteralToken,DimensionToken,PercentageToken

from http import HTTPStatus

class IdentName():
    margin_right='margin-right'
    margin_left='margin-left'
    margin_bottom='margin-bottom'
    margin_top='margin-top'
    letter_spacing='letter-spacing'
    line_height='line-height'
    text_align='text-align'
    font_size='font-size'


def config_font_size(custom_rule:list,size:float,unit:str)->List[Node]:
    config_dimension(custom_rule,'font-size',size,unit)
    return custom_rule

def config_font_size(custom_rule:list,size:float,unit:str)->List[Node]:
    config_dimension(custom_rule,'font-size',size,unit)
    return custom_rule

def config_dimension(custom_rule:list,ident_key:str,size:float,unit:str)->List[Node]:
    node=DimensionToken(0,0,size,int(size),str(size),unit)
    config_node(custom_rule,ident_key,node)
    return custom_rule

def config_percentage(custom_rule:list,ident_key:str,percent:float)->List[Node]:
    node=PercentageToken(0,0,percent,int(percent),str(percent))
    config_node(custom_rule,ident_key,node)
    return custom_rule

def config_ident(custom_rule:list,ident_key:str,ident_val:str)->List[Node]:
    node=IdentToken(0,0,ident_val)
    config_node(custom_rule,ident_key,node)
    return custom_rule

def config_node(custom_rule:list,ident_key:str,node:Node)->List[Node]:
    custom_rule.append(WhitespaceToken(0,0,'\n    '))
    custom_rule.append(IdentToken(0,0,ident_key))
    custom_rule.append(LiteralToken(0,0,':'))
    custom_rule.append(node)
    custom_rule.append(LiteralToken(0,0,';'))
    return custom_rule

def config_prelude(ident_key:str)->List[Node]:
    custom_prelude=[]
    custom_prelude.append(LiteralToken(0,0,'.'))
    custom_prelude.append(IdentToken(0,0,ident_key))
    custom_prelude.append(WhitespaceToken(0,0,' '))
    return custom_prelude
    # <LiteralToken .>
    # <IdentToken calibre6>
    # <WhitespaceToken>

def custom_config(rules:list,font_size=2.0,font_unit='em',margin_right=50,margin_left=50,margin_top=65,margin_bottom=65,letter_spacing=2,line_height=150,text_align='left'):
    config_font_size(rules,font_size,font_unit)
    config_dimension(rules,IdentName.margin_right,margin_left,'px')
    config_dimension(rules,IdentName.margin_left,margin_right,'px')
    config_dimension(rules,IdentName.margin_top,margin_top,'px')
    config_dimension(rules,IdentName.margin_bottom,margin_bottom,'px')
    config_dimension(rules,IdentName.letter_spacing,letter_spacing,'px')
    config_percentage(rules,IdentName.line_height,line_height)
    config_ident(rules,IdentName.text_align,text_align)

def custom_rule(prelude_ident:str,font_size=2.0,font_unit='em',margin_right=50,margin_left=50,margin_top=65,margin_bottom=65,letter_spacing=2,line_height=150,text_align='left')->QualifiedRule:
    rules=[]
    custom_config(rules,font_size,font_unit,margin_right,margin_left,margin_top,margin_bottom, letter_spacing,line_height,text_align)
    prelude=config_prelude(prelude_ident)
    return QualifiedRule(1,2,prelude,rules)
    

def default_rule(prelude_ident:str)->QualifiedRule:
    rules=[]
    config_font_size(rules,2.0,'em')
    config_dimension(rules,IdentName.margin_right,55,'px')
    config_dimension(rules,IdentName.margin_left,55,'px')
    config_dimension(rules,IdentName.margin_right,65,'px')
    config_dimension(rules,IdentName.margin_left,65,'px')
    config_dimension(rules,IdentName.letter_spacing,2,'px')
    config_percentage(rules,IdentName.line_height,150)
    config_ident(rules,IdentName.text_align,'left')
    prelude=config_prelude(prelude_ident)
    return QualifiedRule(1,2,prelude,rules)


if __name__=='__main__':
    rules=[]
    config_font_size(rules,2.0,'em')
    config_dimension(rules,IdentName.margin_right,50,'px')
    config_dimension(rules,IdentName.margin_left,50,'px')
    config_dimension(rules,'letter-spacing',2,'px')
    config_percentage(rules,'line-height',150)
    config_ident(rules,'text-aligh','left')

    print(rules)
    # print(rules.serialize())
    prelude=config_prelude('calibre6')
    print(QualifiedRule(1,2,prelude,rules).serialize())
