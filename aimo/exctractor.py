import os
import re

def splitBlock(content):
    '''
    输入读取到的数组 数组中每行为ini文件中的一行
    对ini进行parser 将组与组之间分割开
    实际上使用'\n\n'也能进行分块
    但是考虑到书写可能不规范的问题 故使用这种稳妥的实现方法
    '''
    blockDict = {}
    ptnSplit = re.compile('\[(\S)+\]')
    hasOldFlag = 0
    blockFlag = 0
    for lineNum,line in enumerate(content,start=1):
        if re.match(ptnSplit,line):
            if hasOldFlag == 1:
                blockDict[tempDict['id']] = tempDict
            tempDict = {}
            hasOldFlag = 1
            blockFlag = 1
            tempDict['id'] = line.replace('[','').replace(']','')
            tempDict['startLineNum'] = lineNum
            tempDict['item'] = []
            continue
        if blockFlag == 1:
            tempDict['item'].append((line,lineNum))
            continue
    blockDict[tempDict['id']] = tempDict
    return blockDict

def getRegeList(blockList):
    '''
    通过对划分好的区块的分析 提取出注册单位 脚本 小队 的ID列表
    注册的单位在
    [TaskForces]组中
    注册的脚本在
    [ScriptTypes]组中
    注册的小队在
    [TeamTypes]组中
    提取之后形成一个dict每个注册的ID为键 对用的注册的顺序序号为值
    '''
    rstDict = {}
    regName = ['TeamTypes','ScriptTypes','TaskForces']
    for name in regName:
        rstDict[name] = {}
        for item in blockList[name]['item']:
            if len(item[0]) == 0:
                continue
            itemRegNum,itemID = item[0].split('=')
            rstDict[name][itemID] = itemRegNum
    return rstDict


def getAITriggerTypes(blockList):
    '''
    [AITriggerTypes]
    将脚本描述列表抓出
    进行归类分析 分为
    ID Name TT1(TeamType) Country Tec Trigger UnitName Condition BaseWeight MinWeight MaxWeight Encounter(遭遇战FLAG) Unknown Side BaseDefence 
    TT2(TeamType)
    Easy Middle Hard
    一共19个项目 部分脚本可能有空 则在字典里写空
    '''
    # 以触发器ID为id 值存当前触发器的内容信息 18条 也为字典
    triggerDict = {}
    triggerList = [script[0] for script in blockList['AITriggerTypes']['item']]
    startLineNum = blockList['AITriggerTypes']['startLineNum']
    for offset,line in enumerate(triggerList,start=1):
        items = line.split(',')
        #若第一列缺失 则定义为无效行（没有ID）跳过
        if len(items[0]) == 0:
            continue
        tempDict = {}
        tempDict['ID'],tempDict['Name'] = items[0].split('=')
        tempDict['TT1'] = items[1] if items[1] !='' else None
        tempDict['Country'] = items[2] if items[2] !='' else None
        tempDict['Tec'] = items[3] if items[3] !='' else None
        tempDict['Trigger'] = items[4] if items[4] !='' else None
        tempDict['UnitName'] = items[5] if items[5] !='' else None
        tempDict['Condition'] = items[6] if items[6] !='' else None
        tempDict['BaseWeight'] = items[7] if items[7] !='' else None
        tempDict['MinWeight'] = items[8] if items[8] !='' else None
        tempDict['MaxWeight'] = items[9] if items[9] !='' else None
        tempDict['Encounter'] = items[10] if items[10] !='' else None
        tempDict['Unkown'] = items[11] if items[11] !='' else None
        tempDict['Side'] = items[12] if items[12] !='' else None
        tempDict['BaseDefence'] = items[13] if items[13] !='' else None
        tempDict['TT2'] = items[14] if items[14] !='' else None
        tempDict['Easy'] = items[15] if items[15] !='' else None
        tempDict['Middle'] = items[16] if items[16] !='' else None
        tempDict['Hard'] = items[17] if items[17] !='' else None
        tempDict['LineNum'] = str(startLineNum + offset)
        triggerDict[tempDict['ID']] = tempDict
    return triggerDict

def getTTNode(rID,blockList):
    '''
    根据id以及分析得到的区块对象
    查找并返回该TeamType的内容 以字典形式给出
    作战小队的提取
    '''
    ttDict = {}
    items = [item[0] for item in blockList[rID]['item']]
    startLineNum = blockList[rID]['startLineNum']
    for item in items:
        if len(item) == 0:
            continue
        key,val = item.split('=')
        ttDict[key] = val
    ttDict['startLineNum'] = startLineNum
    return ttDict

def getTFNode(rID,blockList):
    '''
    根据id以及分析得到的区块对象
    查找并返回TaskForces的内容 字典形式给出
    作战部队的提取
    '''
    tfDict = {}
    items = [item[0] for item in blockList[rID]['item'] if item[0]!='']
    startLineNum = blockList[rID]['startLineNum']
    tfName,valN = items[0].split('=')
    tfGroup,valG = items[-1].split('=')
    tfDict[tfName] = valN
    tfDict[tfGroup] = valG
    for item in items[1:-1]:
        if len(item) == 0:
            continue
        key,val = item.split('=')
        tempDict = {}
        tempDict['amount'],tempDict['unit'] = val.split(',')
        tfDict[key] = tempDict
    tfDict['startLineNum'] = startLineNum
    return tfDict

def getSTNode(rID,blockList):
    '''
    根据id以及分析得到的区块对象
    查找并返回ScriptType的内容 字典形式给出
    脚本序列的提取
    '''
    stDict = {}
    items = [item[0] for item in blockList[rID]['item'] if item[0]!='']
    stName,valN = items[0].split('=')
    startLineNum = blockList[rID]['startLineNum']
    stDict[stName] = valN
    for item in items[1:]:
        stID,val = item.split('=')
        action,para = val.split(',')
        tempDict = {}
        tempDict['action'] = action
        tempDict['para'] = para
        stDict[stID] = tempDict
    stDict['startLineNum'] = startLineNum
    return stDict

'''
进行结果输出
分析触发语句

对作战小队12的ID进行查询
找出对应的作战部队信息和脚本序列信息
输出所有信息
'''
def getTriggerTT(triggerID,triggerDict):
    '''
    从触发语句中找出作战小队12
    '''
    return [triggerDict[triggerID]['TT1'],triggerDict[triggerID]['TT2']]

def getSTTFFromTT(ttDict):
    '''
    从作战小队中提取作战部队和脚本序列的ID
    输入指定的ttDict 取出对应的二者
    '''
    return ttDict['Script'],ttDict['TaskForce']

def triggerStrOutput(triggerID,triggerDict,unitDict):
    '''
    输出指定的内容 附带键值
    '''
    triggerStr = ''
    conditionDict = {
        '0':'<',
        '1':'<=',
        '2':'=',
        '3':'>=',
        '4':'>',
        '5':'!='
    }
    triggerInfoSet = ['ID','Name','Condition','BaseWeight','MaxWeight','MinWeight','TT1','TT2']
    for TI in triggerInfoSet:
        if TI == 'Condition':
            cdtn64 = triggerDict[triggerID][TI]
            unitName = triggerDict[triggerID]['UnitName']
            unitNameC = unitDict[unitName] if unitName in unitDict.keys() else '无'
            volumn = 16*int(cdtn64[0]) + int(cdtn64[1])
            judge = conditionDict[cdtn64[9]]
            if unitName == '<none>':
                triggerStr += '{0}:{1}'.format(TI,unitName) + '\t'
                continue
            triggerStr += '{0}:{1}({2}){3}{4}'.format(TI,unitName,unitNameC,judge,str(volumn)) + '\t'
            continue
        unitName = triggerDict[triggerID][TI]
        triggerStr += '{0}:{1}'.format(TI,unitName) + '\t'
    return triggerStr[:-1]

def ttStrOutput(ttDict):
    '''
    输出TeamType要输出的字符串
    因为单位特殊 故输出一个list 最后排版在外部进行
    '''
    ttStr = []
    lineNum = ttDict['startLineNum']
    name = ttDict['Name']
    keySet = list(ttDict.keys())
    keySet.remove('startLineNum')
    for key in keySet:
        ttStr.append(key + ':' + ttDict[key])
    return ttStr

def tfStrOutput(tfDict,unitDict):
    '''
    输出TaskForces要输出的字符串
    unitDict 为外部字典 主要是为了将单位注册名和中文名对应起来
    一行 ALL in
    '''
    tfStr = ''
    lineNum = tfDict['startLineNum']
    name = tfDict['Name']
    group = tfDict['Group']
    keySet = list(tfDict.keys())
    keySet.remove('startLineNum')
    keySet.remove('Name')
    keySet.remove('Group')
    for key in keySet:
        tfC = unitDict[tfDict[key]['unit']] if tfDict[key]['unit'] in unitDict.keys() else '无'
        tfStr += 'Unit:{0} {1}({2})'.format(tfDict[key]['amount'],tfDict[key]['unit'],tfC) + '\t'
    return tfStr[:-1]

def stStrOutput(stDict):
    '''
    输出ScriptType要输出的字符串
    一行 ALL in
    '''
    stStr = ''
    lineNum = stDict['startLineNum']
    name = stDict['Name']
    keySet = list(stDict.keys())
    keySet.remove('Name')
    keySet.remove('startLineNum')
    for key in keySet:
        stStr += 'Action:{0}-->Parameter:{1}'.format(stDict[key]['action'],stDict[key]['para']) + '\t'
    return stStr[:-1]


def loadUnitDict(fname):
    '''
    读取一个 单位注册名 单位 对应字典
    每行一个单位的描述
    用空格分开
    '''
    unitDict = {}
    with open(fname,'r',encoding='utf-8') as file:
        for line in file.readlines():
            unitID,unitName = line.strip().split(' ')
            unitDict[unitID] = unitName
    return unitDict


def outputResult(aimoFileName,outputFileName='./sample.txt'):
    '''
    输出对一个aimo.ini的分析结果
    输入aimo.ini文件名
    最终输出形式为一个完成分析后写出结果的文件 暂定文件名为sample
    '''
    with open(aimoFileName,'r',encoding='utf-8') as file:
        content = [line.strip() for line in file.readlines()]
    blockDict = splitBlock(content)
    triggerDict = getAITriggerTypes(blockDict)
    unitDict = loadUnitDict('./MO3.3单位代码.txt')
    with open(outputFileName,'w',encoding='utf-8') as file:
        for triggerID in triggerDict.keys():
            # 此处写入触发器的部分内容
            file.write(triggerStrOutput(triggerID,triggerDict,unitDict) + '\n')
            ttList = getTriggerTT(triggerID,triggerDict)
            for ttID in ttList:
                if ttID == '<none>':
                    continue
                ttDict = getTTNode(ttID,blockDict)
                ttStrs = ttStrOutput(ttDict)
                # 此处写入TeamTypes中对应的内容 与触发器保持一个|---格式
                file.write('\t[TeamTypes]\n')
                for line in ttStrs:
                    file.write('\t' + '|---' + line + '\n')
                stID,tfID = getSTTFFromTT(ttDict)
                stStr = stStrOutput(getSTNode(stID,blockDict))
                tfStr = tfStrOutput(getTFNode(tfID,blockDict),unitDict)
                file.write('\t\t|---[ScriptTypes]\t{0}\n'.format(stStr))
                file.write('\t\t|---[TaskForces]\t{0}\n'.format(tfStr))


if __name__ == '__main__':
	outputResult('./aimo.ini')