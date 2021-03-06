
##python libaries required
import sys, os, string, math, random, shutil, glob, re
import numpy as np
from random import randint
from time import sleep
from sklearn.externals import joblib
from decimal import Decimal #20141228
from sklearn.cross_validation import cross_val_score
from sklearn.ensemble import RandomForestClassifier,AdaBoostClassifier

##pre-defined parameters for miRLocator
cv = 10
minCandidateMiRNALen = 16
maxCandidateMiRNALen = 30
minPredScore = 0.25
upOffSet = 5
downOffSet = 5
speciesList = ["Arabidopsis thaliana", "Arabidopsis lyrata", "Brassica napus", "Glycine max",  "Medicago truncatula", "Malus domestica", "Prunus persica", "Vitis vinifera","Nicotiana tabacum","Populus trichocarpa", "Solanum tuberosum",  "Brachypodium distachyon", "Oryza sativa", "Zea mays", "Physcomitrella patens" ]





###################################################


##run command line 
def runCommand ( order ):
	res = os.system( order )
	if( res != 0 ):
		print "Error to run order:", order
		sys.exit()
	#end if 
#end fun

##create file dictionary if not exists
def createDict( fileDic ):
	if not os.path.exists( fileDic ):
		os.makedirs( fileDic )
#end fun 

##remove files in one dictionary
def clearnDict( fileDic ):
	r = glob.glob(fileDic + '*')
	for i in r:
   		os.remove(i)
#end fun


##merge list
def mergeList( listID, sep ):
	if( sep == "" ):
		res = ''.join(listID)
	if( sep == "," ):
		res = ','.join(listID)
	if( sep == ";" ):
		res = ';'.join(listID)
	if( sep == ":" ):
		res = ':'.join(listID)
	return res
#end def 

def uniqArrayLen( list2d ):
	lenList = []
	for i in range(len(list2d)):
		lenList.append( len(list2d[i] ) )
	#end for
	lenSet = set(lenList)
	return list(lenSet)
#end def  


##transform list&list to 2-D array
def transform_list_2_array( list2d ):
	Array2d = np.array( list2d )
	return Array2d
#end def

##read lines from a file 
def readLinesFromFile (fileDir):
	fpr = open(fileDir, "r")
	lines = fpr.readlines()
	fpr.close()
	return lines
#end fun



##write lines to a file 
def writeLinesToFile( lineList, endFlag, fileDir ):
	fpw = open( fileDir, "w" )
	for curLine in lineList:
		fpw.write( curLine + endFlag )
	fpw.close()
#end def



##fold pre-miRNAs sequences using RNAfold
def foldPreMiRNASeq( preMiRNADic, RNAfoldDic, tmpFileDir, RNAfoldResDir, path=None ):
  fpw = open(tmpFileDir, "w")
  for curPreMiRNAID in preMiRNADic.keys():
    curPreMiRNASeq = preMiRNADic[curPreMiRNAID]
    fpw.write(">" + curPreMiRNAID + "\n" +  curPreMiRNASeq + "\n" )
  #end for 
  fpw.close()
  
  foldCommand = ('cd {};'.format(path) if path else None) + RNAfoldDic + "RNAfold -p -d2 --noLP < " + tmpFileDir + " > " + RNAfoldResDir
  res = os.system(foldCommand)
  if( res != 0 ):
    print "Error to run RNAfold using the command:", foldCommand
    sys.exit()
  print "fold pre-miRNA sequences successfully.\n"
#end def

##parse RNAfold result
def parseRNAfoldResult( RNAfoldResDir ):
  lines = readLinesFromFile(RNAfoldResDir)
  seqNum = len(lines)/6
  resDic = {}
  for ii in range(seqNum):
    if( (6*ii + 5) > len(lines) ):
      break
    curID = lines[6*ii]
    curID = curID[1:]
    curID = curID.strip()
    curStruct = lines[6*ii+2]
    elements = curStruct.split(" ")
    resDic[curID] = elements[0]
  #end for ii
  return resDic
#end fun



##check file exists
def fileExist(fileDir):
	return os.path.exists(fileDir)
#end fun 	

##remove file
def removeFile(fileDir):
	if(fileExist(fileDir) == True):
		try:
			os.remove(fileDir)
		except:
			print "Warning: Failed to remove ", fileDir
	#end if 
#end fun
  
  

##check input data for training
def checkFileForTraining(fileDir, RNAfoldDic, sourceDic, dpSSFileDic, dpSSFlag = True ):
  newFileDir = fileDir
  lines = readLinesFromFile(fileDir)
  preMiRNADic = {}
  lenList=[]
  for curLine in lines:
    elements = curLine.split("\t")
    curElementLen = len(elements)
    lenList.append(curElementLen)
    if( curElementLen != 4 and curElementLen != 5 ):
      print curLine
      print "Error: format error in the file input for training. For each miRNA per line, there are four or five elements seperated with tab keys, Please check the format:"
      print "miRNA_ID\tpre-miRNA_ID\tmiRNA_sequence\tpre-miRNA_sequence"
      print "or\n"
      print "miRNA_ID\tpre-miRNA_ID\tmiRNA_sequence\tpre-miRNA_sequence\tpre-miRNA_structure\n\n"
      sys.exit()
    else:
      curMiRNAID = elements[0]
      curPreMiRNAID = elements[1]
      curMiRNASeq = elements[2]
      curPreMiRNASeq = elements[3]
      if( curPreMiRNAID not in preMiRNADic.keys() ):
	preMiRNADic[curPreMiRNAID] = curPreMiRNASeq
      #end if
    #end else
   #end for
   
  print len( preMiRNADic.keys() ), " pre-miRNAs, ", len(lines), " miRNAs included"
   
   ##check lenList
  lenList = list( set(lenList) )
  if( len(lenList) > 1 ):
    print "Error: different element number for miRNAs in ", fileDir, " Element number:", lenList
  else:
    
    if( lenList[0] == 5 and dpSSFlag == False ):
      print "Structure and dp_ss have been given.\n"
    else: 
      #structure required
      tmpFileDir = dpSSFileDic + "tmp_seq.txt"
      RNAfileResDir = dpSSFileDic + "tmp_struct.txt"
      foldPreMiRNASeq(preMiRNADic, RNAfoldDic, tmpFileDir, RNAfileResDir,dpSSFileDic )
      structDic = parseRNAfoldResult(RNAfileResDir)
      #removeFile(tmpFileDir)
      #removeFile(RNAfileResDir)
    
      ##copy dp_ps, ss_ps file
    #   if( dpSSFlag == True ):
	# mvCommand = "mv " + sourceDic + "*_dp.ps " + dpSSFileDic
	# runCommand(mvCommand)
	# mvCommand = "mv " + sourceDic + "*_ss.ps " + dpSSFileDic
	# runCommand(mvCommand)
    #   else:
	# rmCommand = "rm " + sourceDic + "*_dp.ps " + dpSSFileDic
	# runCommand(rmCommand)
	# rmCommand = "rm " + sourceDic + "*_ss.ps " + dpSSFileDic
	# runCommand(rmCommand)
      #end else
	
      
      #structure are provided
      if( lenList[0] == 4 ): 
	newFileDir = fileDir + "_ref"
	fpw = open( newFileDir, "w" )
	for curLine in lines:
	  elements = curLine.split("\t")
	  curPreMiRNAID = elements[1]
	  if( curPreMiRNAID not in structDic.keys() ):
	    continue
	  curPreMiRNAStruct = structDic[curPreMiRNAID]
	  fpw.write( curLine.strip() + "\t" + curPreMiRNAStruct + "\n" )
	#end for
	fpw.close() 
      #end if    
    #end else
  #end else
  return newFileDir
#end def




##check input data for training
def checkFileForPrediction(fileDir, RNAfoldDic, sourceDic, dpSSFileDic, dpSSFlag = True ):
  newFileDir = fileDir
  lines = readLinesFromFile(fileDir)
  preMiRNADic = {}
  lenList=[]
  for curLine in lines:
    elements = curLine.split("\t")
    curElementLen = len(elements)
    lenList.append(curElementLen)
    if( curElementLen != 2 and curElementLen != 3 ):
      print curLine
      print "Error: format error in the file input for prediction. For each miRNA per line, there are two or three elements seperated with tab keys, Please check the format:"
      print "pre-miRNA_ID\tpre-miRNA_sequence"
      print "or\n"
      print "pre-miRNA_ID\tpre-miRNA_sequence\tpre-miRNA_structure\n\n"
      sys.exit()
    else:
      curPreMiRNAID = elements[0]
      curPreMiRNASeq = elements[1]
      if( curPreMiRNAID not in preMiRNADic.keys() ):
	preMiRNADic[curPreMiRNAID] = curPreMiRNASeq
      #end if
    #end else
   #end for
   
  print len( preMiRNADic.keys() ), " pre-miRNAs for prediction\n"
   
   ##check lenList
  lenList = list( set(lenList) )
  if( len(lenList) > 1 ):
    print "Error: different element number for pre-miRNAs in ", fileDir, " Element number:", lenList
  else:
    if( lenList[0] == 3 and dpSSFlag == False ):
      print "Structure and dp_ss have been given.\n"
    else: 
      #structure required
      tmpFileDir = dpSSFileDic + "tmp_seq.txt"
      RNAfileResDir = dpSSFileDic + "tmp_struct.txt"
      foldPreMiRNASeq(preMiRNADic, RNAfoldDic, tmpFileDir, RNAfileResDir,dpSSFileDic )
      structDic = parseRNAfoldResult(RNAfileResDir)
      #removeFile(tmpFileDir)
      #removeFile(RNAfileResDir)
    
      ##copy dp_ps, ss_ps file
    #   if( dpSSFlag == True ):
	# mvCommand = "mv " + sourceDic + "*_dp.ps " + dpSSFileDic
	# runCommand(mvCommand)
	# mvCommand = "mv " + sourceDic + "*_ss.ps " + dpSSFileDic
	# runCommand(mvCommand)
    #   else:
	# rmCommand = "rm " + sourceDic + "*_dp.ps " + dpSSFileDic
	# runCommand(rmCommand)
	# rmCommand = "rm " + sourceDic + "*_ss.ps " + dpSSFileDic
	# runCommand(rmCommand)
      #end else
	
      
      #structure are provided
      if( lenList[0] == 2 ): 
	newFileDir = fileDir + "_ref"
	fpw = open( newFileDir, "w" )
	for curLine in lines:
	  elements = curLine.split("\t")
	  curPreMiRNAID = elements[1]
	  if( curPreMiRNAID not in structDic.keys() ):
	    continue
	  curPreMiRNAStruct = structDic[curPreMiRNAID]
	  fpw.write( curLine.strip() + "\t" + curPreMiRNAStruct + "\n" )
	#end for
	fpw.close() 
    #end if    
  #end else
  return newFileDir
#end def




################################################################################################
##function: read pre-miRNA sequences and structures#############################################
################################################################################################
def readSequenceAndStructure( SeqStructFileDir):
	allInfo = list()
	for line in open(SeqStructFileDir):
		line = line.strip()
		[miRNAID, pre_MiRNAID, mut_miRNASeq, pre_miRNASeq, pre_miRNAStruct] = line.split("\t")
		allInfo.append( [miRNAID, pre_MiRNAID, mut_miRNASeq, pre_miRNASeq, pre_miRNAStruct] )
	#end for
	return allInfo
#end fun



###check miRNA located in which arm
def checkArm( RNASequence, RNAStructure, miRNASeq ):
	if( getMirnaIncludedInLoop( RNASequence, RNAStructure, miRNASeq ) ):
		return "loop"
	#check arms
	mirnaStruct = getMiRNAStructure( miRNASeq, RNASequence, RNAStructure )
	arm = "unmatchedRegion"
	if( '(' in mirnaStruct ):
		arm = "arm5"
	if( ')' in mirnaStruct ):
		arm = "arm3"
	return arm
#end fun

##remove mature miRNA in loops
def removeMiRNAInLoop( allSeq ):
	res = []
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		curArmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
		
		if( curArmType != "arm3" and curArmType != "arm5" ):
			continue
		res.append( allSeq[i] )
	#end for i
	return res
#end fun



##remove multiple miRNAs on one pre-miRNA arm
def removeMultipleMiRNAsOneArm ( allSeq ):
	armStat_Dic = {}
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		curArmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
		
		if( curArmType != "arm3" and curArmType != "arm5" ):
			continue
		
		if( curPreMiRNAID not in armStat_Dic ):
			armStat_Dic[curPreMiRNAID] = [0,0]
		tmp = armStat_Dic[curPreMiRNAID]
		if( curArmType == "arm5" ):
			tmp[0] = tmp[0] + 1
		else:
			tmp[1] = tmp[1] + 1
		armStat_Dic[curPreMiRNAID] = tmp	
	#end for i
	#print armStat_Dic
	
	removedPreMiRNAs = []
	res = []
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		#no miRNA on 5' and 3' arms
		if( curPreMiRNAID not in armStat_Dic ):
			removedPreMiRNAs.append(curPreMiRNAID) 
			continue
		#no multiple miRNAs on one arm
		armStatList = armStat_Dic[curPreMiRNAID]
		if( (armStatList[0] > 1) or (armStatList[1] > 1) ):
			print curPreMiRNAID, "multiple mature miRNAs on one arm, will be removed."
			removedPreMiRNAs.append(curPreMiRNAID) 
			continue
		
		res.append( allSeq[i] )
	#end for i
	
	arm5 = 0
	arm3 = 0
	armBoth = 0
	for curKey in armStat_Dic.keys():
		if( curKey in removedPreMiRNAs ):
			continue
		 
		armStatList = armStat_Dic[curKey]
		if( (armStatList[0] > 1) or (armStatList[1] > 1) ):
			continue
		if( (armStatList[0] == 1) and (armStatList[1] == 0) ):
			arm5 = arm5 + 1
		if( (armStatList[0] == 0) and (armStatList[1] == 1) ):
			arm3 = arm3 + 1
		if( (armStatList[0] == 1) and (armStatList[1] == 1) ):
			armBoth = armBoth + 1
	#end for curKey
	print "miRNAs: Arm5\t", arm5, "\tarm3\t", arm3, "\tarmBoth\t", armBoth
	
	
	return res
#end fun


##save sequence list
def saveSeq2File(allSeq, FileDir):		
	fpw = open(FileDir, "w")
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		fpw.write(curMiRNAID + "\t" + curPreMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n")
	#for i
	fpw.close()
#end def

##get miRNA length
def getMiRNALen (miRNASeq):
	return len(miRNASeq)
#end def


####check whether there is a loop in mature miRNA
def getMirnaIncludedInLoop( RNASequence, RNAStructure, miRNASeq ):
	flag = False
	mirnaStruct = getMiRNAStructure( miRNASeq, RNASequence, RNAStructure )
	if( ('(' in mirnaStruct) and (')' in mirnaStruct) ):
		flag = True
	return flag
#end fun



##get miRNA structure
def getMiRNAStructure (miRNASeq, RNASequence, RNAStructure ):
	[startPos, endPos] = getMiRNAPosition( miRNASeq, RNASequence )
	mirnaStruct = RNAStructure[ startPos:endPos ]
	return mirnaStruct
#end fun


##get miRNA position on RNASequence, 0-based
def getMiRNAPosition (miRNASeq, RNASequence ):
	startPos = RNASequence.find(miRNASeq)
	endPos = startPos + getMiRNALen(miRNASeq)
	return [startPos, endPos]
#end fun




def matchRNAStructure( RNAStructure ):
	RNALen = len(RNAStructure)
	#first define a list with the same length of RNAStructure, at each position
	#the value of matched position for current position
	matchedPosList = [-1]*RNALen
	
	stack = []
	stackPos = []
	for i in range(RNALen):
		a = RNAStructure[i]
		if( isParenthese(a) == False ):
			continue
		if( len(stack) == 0 ):
			#empty stack, record item
			stack.append(a)
			stackPos.append(i)
		else:
			#get last item in stack and stackPos
			stack_lastItem = stack.pop()
			stackPos_lastItem = stackPos.pop()
			if( stack_lastItem == '(' and a == ')' ):
				#meet a match, record matched position
				matchedPosList[i] = stackPos_lastItem
				matchedPosList[stackPos_lastItem] = i
				continue
			else:
				#have to record
				stack.append( stack_lastItem )
				stackPos.append( stackPos_lastItem )
				stack.append(a)
				stackPos.append(i)
			#end else
		#end else
	#end for i
	return matchedPosList
#end fun

def getMatchedPositions( startPos, endPos, matchedStructList ):
	RNALen = len(matchedStructList)
	#check pos
	if( startPos < 0 ):
		startPos = 0
	if( endPos < 0 ):
		endPos = endPos
	if( startPos > RNALen ):
		startPos = RNALen - 1
	if( endPos > RNALen ):
		endPos = RNALen - 1
	
	if( startPos == 0 and endPos == 0 ):
		return [0,0]
	
	matchedPosList = []
	for i in range(startPos, endPos):
		curPos = matchedStructList[i]
		matchedPosList.append( curPos )
	#end for i
	
	if( matchedPosList[0] == -1 ):
		idx = 0
		for i in range(len(matchedPosList)):
			if( matchedPosList[i] != -1 ):
				idx = i
				break 
		#end for i
		matchedPos = matchedPosList[idx]
		idxList = range(idx)
		for i in idxList[::-1]:
			matchedPos = matchedPos + 1
			matchedPosList[i] = matchedPos
		#end for i
	#end if
	if( matchedPosList[-1] == -1 ):
		idxList = range(len(matchedPosList))
		idx = 0
		for i in idxList[::-1]:
			if( matchedPosList[i] != -1 ):
				idx = i
				break
		#end for i
		matchedPos =  matchedPosList[idx]
		idx = idx + 1
		for i in range(idx, len(matchedPosList)):
			matchedPos = matchedPos - 1
			matchedPosList[i] = matchedPos
	#end if
	if( matchedPosList[0] < 0 ):
		matchedPosList[0] = 0
	if( matchedPosList[0] > RNALen ):
		matchedPosList[0] = RNALen - 1
	if( matchedPosList[-1] < 0 ):
		matchedPosList[-1] = 0
	if( matchedPosList[-1] > RNALen ):
		matchedPosList[-1] = RNALen - 1
			
	return [matchedPosList[0], matchedPosList[-1]]
#end fun


##remove duplicate pre-miRNA sequence (one pre-miRNA, two anntoated mature miRNAs for arm 5 and 3)
def refinePreMiRNASeq( allSeq ):
	
	allSeq_RefDic = {}
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		curArmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
		
		if( curArmType != "arm3" and curArmType != "arm5" ):
			continue
			
		if( curPreMiRNAID not in allSeq_RefDic.keys() ):
			allSeq_RefDic[curPreMiRNAID] = allSeq[i]
		else:
			if( curArmType != "arm3" ):
				allSeq_RefDic[curPreMiRNAID] = allSeq[i]
		#end else
		
	#end for i
	
	#recheck, remove multiple miRNAs on one arm
	resDic = []
	for curKey in allSeq_RefDic.keys():
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq_RefDic[curKey]
		resDic.append( allSeq_RefDic[curKey] )
	#end for
			
	return resDic 
#end fun


##arm transform for mature miRNA 
def armTransform( allSeq ):
	res = []
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		armType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
		if( armType == "arm3" ):
			curMiRNAStar = getMiRNAStar(curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq)
			res.append( [curMiRNAID, curPreMiRNAID, curMiRNAStar, curPreMiRNASeq, curPreMiRNAStructure] )
		else:
			res.append( allSeq[i] )
		#end else
	#end for i
	return res
#end fun



##get miRNA GC content
def getGCContent (miRNASeq):
	Len = getMiRNALen(miRNASeq)
	gc = miRNASeq.count('G')
	gc = gc + miRNASeq.count('g')
	gc = gc + miRNASeq.count('C')
	gc = gc + miRNASeq.count('c')
	GCContent = 1.0*gc/Len
	return GCContent
#end def 


##get min and max values
def getMinMaxInArray( Array ):
	Min = 1000000000000
	Max = 0
	for i in range( len(Array) ):
		curValue = float(Array[i])
		if( curValue < Min ):
			Min = curValue
		if( curValue > Max ):
			Max = curValue
	#end for i
	return [Min, Max]
#end fun

##normalize Array to 0~1
def normalizeArray( Array ):
	[Min, Max] = getMinMaxInArray(Array)
	deltValue = Max - Min
	ArrayNew = [0]*len(Array)
	for i in range( len(ArrayNew) ):
		curValue = float( Array[i] )
		ArrayNew[i] = 1.0*(curValue - Min)/deltValue
	#end for i
	return ArrayNew
#end fun

################################################################################################
##check RNASequence, whether gap or white space column##########################################
################################################################################################
def checkSequenceAndStructure( RNASequence, RNAStructure ):
	Seq = RNASequence
	Str = RNAStructure
	# Remove gap positions from sequence (and structure)
	i = 0
	while i < len(Seq):
		if Seq[i] in "- ":
			# Gap or white space column
			Seq = Seq[:i] + Seq[i + 1:]
			Str = Str[:i] + Str[i + 1:]
		else:
			i += 1
	#end while 
	if( len(RNASequence) != len(Seq) ):
		sys.exit("Error: gap or white space in sequence.")
#end fun

def isParenthese(ch):
	if( ch=='(' or ch==')' ):
		return True
	else:
		return False
#end fun

###############################################################################################
########Complement a string of IUPAC DNA nucleotides (output A C T G only).####################
########The string input are one-letter upper or lower case IUPAC nucleotides to complement.####
########A complemented string, ie A->T, T->A, C->G, G->C, U->A. Case is preserved.###############
################################################################################################
def nucleotideComplement (ch):
	str = 'ACGTUacgtu'
	chDict = {'A': 'U', 'U':'A', 'C':'G', 'G':'C', 'a': 'u', 'u':'a', 'c':'g', 'g':'c' }
	if( ch not in str ):
		return ch 
	else:
		return chDict[ch]
#end fun

def dnaComplement( s ):	
	cgene = list(s)
	for i in range( len(cgene) ):
		cgene[i] = nucleotideComplement( cgene[i] )
	#end for  
	str = ''.join(cgene)
	return str
#end fun

def dnaReverseComplement(s):
	s_c = dnaComplement(s)
	return s_c[::-1]
#end fun

################################################################################################
################################################################################################


##get complementarity region
def computeComplementaritySequence(RNASequence, RNAStructure, miRNASeq, matchedStructList = [] ):
	
	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure( RNAStructure )
	[mirnaStart, mirnaEnd] = getMiRNAPosition(miRNASeq, RNASequence)
	[matchedPosStart, matchedPosEnd] = getMatchedPositions( mirnaStart, mirnaEnd, matchedStructList ) 
	#print mirnaStart, "..", mirnaEnd, "\tmatchedPos:", matchedPosStart, "..", matchedPosEnd, RNASequence[matchedPosEnd:matchedPosStart+1], "\n"
	if( matchedPosStart == 0 and matchedPosEnd == 0 ):
		return 'N'*len(miRNASeq)
	
	################################################################################
	
	if( matchedPosStart < matchedPosEnd ):
		return RNASequence[matchedPosStart: (matchedPosEnd+1)]
	else:
		subStr = RNASequence[matchedPosEnd: (matchedPosStart+1)]
		return subStr[::-1]
	#end else
	
	size = getMiRNALen(miRNASeq)
	[mirnaStart, mirnaEnd] = getMiRNAPosition(miRNASeq, RNASequence)
	armType = checkArm( RNASequence, RNAStructure, miRNASeq )
	miRNAStar = ""
	if(armType == "arm5"):
		#check whether there loop before miRNA
		startToMirna = RNAStructure[0:mirnaStart]
		#print RNASequence[0:mirnaStart]
		#get open parenthesis minus close parenthesis between precursor start and mirna
		openPar = startToMirna.count( '(') - startToMirna.count( ')' )
		
		#analysing from the end of precursor if presence of loop
		openParEnd=0
		i=len(RNAStructure)-1
		while ( openPar != openParEnd ):
			if( RNAStructure[i]== ')' ):
				openParEnd = openParEnd + 1
			if( RNAStructure[i]== '(' ):
				openParEnd = openParEnd - 1
			if(openPar != openParEnd):
				i = i - 1        
		#end while
		
        #get complement
		star=""
		posOnStar = i
		i = mirnaStart
		while( i >= mirnaStart and i < mirnaEnd ):
			posOnStar = posOnStar - 1
			a = RNAStructure[i]
			b = RNAStructure[posOnStar]
			#print i, RNASequence[i], a, posOnStar, RNASequence[posOnStar], b 
			#for bulge before miRNA start position
			if( i == mirnaStart and isParenthese(a) == True and isParenthese(b) == False ):
				continue
			if( isParenthese(a) == True and isParenthese(b) == True or a==b ):
				star = star + RNASequence[posOnStar]
			elif( a =='.' and isParenthese(b) == True ):
				posOnStar = posOnStar + 1
			elif( b =='.' and isParenthese(a) == True ):
				star = star + RNASequence[posOnStar]
				i = i - 1
			i = i + 1
		#end for i
		miRNAStar = star[::-1]
	elif( armType == "arm3"):
		#end for 3'
		EndToMirna = RNAStructure[mirnaStart+size: len(RNAStructure)]
		#print EndToMirna, miRNA, RNAStructure[mirnaStart:(mirnaStart+size)], RNASequence[mirnaStart+size: len(RNAStructure)]
        #get open parenthesis minus close parenthesis between precursor end and mirna end
		closePar= EndToMirna.count( ')') - EndToMirna.count( '(');
		#print closePar
		
		#analysing from the end of precursor if presence of loop
		openPar = 0
		i = 0
		while( openPar != closePar ):
			if( RNAStructure[i] == '(' ):
				openPar = openPar + 1
			if( RNAStructure[i] == ')' ):
				openPar = openPar - 1
			if( openPar != closePar ):
				i = i + 1
		#end while
		print i 
		
		
		#get complement            
		star=""
		posOnStar = i
		#print RNAStructure[posOnStar + 1: posOnStar+ 31]
		idxVec = range( mirnaStart, mirnaEnd )
		i = mirnaEnd - 1
		while( i >= mirnaStart and i < mirnaEnd ):
			posOnStar = posOnStar + 1
			a = RNAStructure[i]
			b = RNAStructure[posOnStar]
			#print RNASequence[i], RNASequence[posOnStar], a, b
			#for a bulge after the miRNA end position
			if( isParenthese(a) and i == (mirnaEnd - 1) and isParenthese(b) == False ):
				continue
			
			if( isParenthese(a) and isParenthese(b) or a==b ):
				star = star + RNASequence[posOnStar]
			elif( a == '.' and isParenthese(b) ):
				posOnStar = posOnStar - 1
			elif( b =='.' and isParenthese(a) ):
				star = star + RNASequence[posOnStar]
				i = i + 1
			#end if
			i = i - 1
        #end while
		miRNAStar = star[::-1]
	else:
		miRNAStar = 'N'*len(miRNASeq)
    #end if..else
	return miRNAStar
#end fun

########################################################################
##get miRNAStar#########################################################
########################################################################
def getMiRNAStar(RNASequence, RNAStructure, miRNASeq, matchedStructList = [] ):
	
	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure( RNAStructure )
	[miRNAPosStart, miRNAPosEnd] = getMiRNAPosition( miRNASeq, RNASequence )
	[matchedPosStart, matchedPosEnd] = getMatchedPositions( miRNAPosStart, miRNAPosEnd, matchedStructList )
	matchedPosStart = matchedPosStart + 2
	matchedPosEnd = matchedPosEnd + 2
	RNALen = len(RNASequence)
	if( matchedPosStart > RNALen ):
		matchedPosStart = RNALen - 1
	if( matchedPosEnd > RNALen ):
		matchedPosEnd = RNALen - 1
	
	starSeq = ""
	if( matchedPosStart < matchedPosEnd ):
		starSeq = RNASequence[matchedPosStart: (matchedPosEnd+1)]
		starSeq = starSeq[::-1]
	else:
		starSeq = RNASequence[matchedPosEnd: (matchedPosStart+1)]
		
	return starSeq
	
#end fun


########################################################################
####################calculate MFE#######################################
########################################################################
#RNAfold.exe --noPS -a
def calculateMFE( miRNASeq, miRNAStarSeq, RNAfolderDic, tempFileDir ):
	#save sequence to tempFileDir
	#print miRNASeq, miRNAStarSeq
	fpw = open( tempFileDir, 'w')
	fpw.write( ">miRNASeq" + "\n" + miRNASeq + "\n" + ">miRNAStarSeq" + "\n" + miRNAStarSeq + "\n" )
	fpw.close()
	
	resultFileDir = tempFileDir + "_result"
	order = RNAfolderDic + "RNAduplex < " + tempFileDir + " > " +  resultFileDir
	
	res = os.system( order )
	if( res != 0 ):
		print "Error to run RNAduplex for calculating MFE for miRNASeq:", miRNASeq, " and miRNAStarSeq:", miRNAStarSeq 
		sys.exit()
	#end if 
	
	#get MFE
	lines = readLinesFromFile(resultFileDir)
	if( len(lines) != 3 ):
		print resultFileDir
		sys.exit( "Error: line number is not THREE in RNAduplex output file:" )
	lastLine = lines[-1]
	lastLine = lastLine.strip()
	items = lastLine.split("(")
	lastItem = items[-1]
	MFE = lastItem.replace(")", "")

	removeFile( tempFileDir )
	removeFile(resultFileDir)
	return MFE
#end fun 



#Maximum length on the miRNA without bulges
def getMaximumLengthWithoutBulges(mirnaStruct):
	Len = Max = 0
	for i in range(len(mirnaStruct)):
		ch = mirnaStruct[i]
		if( ch == '(' or ch == ')' ):
			Len = Len + 1
		else:
			Len = 0
		if( Max < Len ):
			Max = Len
	#end for i 
	return Max
#end fun

#Maximum length on the miRNA without bulges in percentage
def getMaximumLengthWithoutBulgesPerc( mirnaStruct ):
	b = getMaximumLengthWithoutBulges( mirnaStruct )
	pc = 1.0*b/len(mirnaStruct)
	return pc
#end fun

#Base pairs in duplexe miRNA-miRNA*
def getBasePairsInDuplex( mirnaStruct ):
	p = mirnaStruct.count( '(' ) + mirnaStruct.count( ')' )
	return p
#end fun 

##20mer base paired
def getPresenceOfPerfect20MerBasePair(mirnaStruct):
	if( mirnaStruct.find( "((((((((((((((((((((" ) >= 0 or mirnaStruct.find( ")))))))))))))))))))))" ) >= 0 ):
		return 1
	else:
		return 0
#end fun

##start of 20mer base paired
def getStartOfPerfect20MerBasePair(mirnaStruct):
	if( getPresenceOfPerfect20MerBasePair(mirnaStruct) == 1 ):
		s = mirnaStruct.find("((((((((((((((((((((")
		if( s == -1 ):
			s = mirnaStruct.find(")))))))))))))))))))))")
		return s+1
	else:
		return -1
#end fun 




##10mer base paired
def getPresenceOfPerfect10MerBasePair(mirnaStruct):
	if( mirnaStruct.find( "((((((((((" ) >= 0 or mirnaStruct.find( "))))))))))" ) >= 0 ):
		return 1
	else:
		return 0
#end fun

##start of 10mer base paired
def getStartOfPerfect10MerBasePair(mirnaStruct):
	if( getPresenceOfPerfect10MerBasePair(mirnaStruct) == 1 ):
		s = mirnaStruct.find("((((((((((")
		if( s == -1 ):
			s = mirnaStruct.find("))))))))))")
		return s+1
	else:
		return -1
#end fun 

##5mer base paired
def getPresenceOfPerfect5MerBasePair(mirnaStruct):
	if( mirnaStruct.find( "(((((" ) >= 0 or mirnaStruct.find( ")))))" ) >= 0 ):
		return 1
	else:
		return 0
#end fun


##start of 5mer base paired
def getStartOfPerfect5MerBasePair(mirnaStruct):
	if( getPresenceOfPerfect5MerBasePair(mirnaStruct) == 1 ):
		s = mirnaStruct.find("(((((")
		if( s == -1 ):
			s = mirnaStruct.find(")))))")
		return s+1
	else:
		return -1
#end fun 


	
		



#Distance from terminal loop
def getDistanceFromTerminalLoop(miRNASeq, RNASequence, RNAStructure):
	armCheck = checkArm(RNASequence, RNAStructure, miRNASeq)
	[miRNAStartPos, miRNAEndPos] = getMiRNAPosition (miRNASeq, RNASequence )
	if( armCheck == "arm5" ):
		leftRNAStruct = RNAStructure[ miRNAStartPos: len(RNAStructure)]
		closestLoopEndPar = leftRNAStruct.find(')') + miRNAStartPos
		leftRNAStruct = RNAStructure[ miRNAStartPos: closestLoopEndPar ]
		loopStart = leftRNAStruct.rfind( '(' ) + miRNAStartPos
		res = loopStart - (miRNAStartPos + len(miRNASeq) - 1 )
		return res
	elif( armCheck == "arm3" ):
		leftRNAStruct = RNAStructure[ 0: miRNAStartPos]
		closestLoopOpenPar = leftRNAStruct.rfind( '(' )
		leftRNAStruct = RNAStructure[ closestLoopOpenPar: miRNAStartPos ]
		loopEnd = leftRNAStruct.find( ')' ) + closestLoopOpenPar
		res = miRNAStartPos - loopEnd
		return res
	else:
		return -1
	#end else
#end fun 


#Distance from start of the hairpin
def getDistanceFromHairpinStart(miRNASeq, RNASequence, RNAStructure):
	armCheck = checkArm( RNASequence, RNAStructure, miRNASeq)
	[miRNAStartPos, miRNAEndPos] = getMiRNAPosition (miRNASeq, RNASequence )
	if( armCheck == "arm5" ):
		return miRNAStartPos
	elif( armCheck == "arm3" ):
		return len(RNAStructure) - miRNAStartPos - len(miRNASeq)
	else:
		if ')' not in RNAStructure:
			return miRNAStartPos
		elif '(' not in RNAStructure:
			return len(RNAStructure) - miRNAStartPos - len(miRNASeq)
		else:
			return miRNAStartPos
	#end else
#end fun

##get average number base pairs in window w
def getAverageNumberOfBasePairInWindow( mirnaStruct, w ):
	numList = []
	total = 0
	for i in range(len(mirnaStruct) - w):
		subStruct = mirnaStruct[i:i+w+1]
		m1 = subStruct.count( "(")
		m2 = subStruct.count( ")")
		numList.append( m1 + m2 )
		total = total + m1
		total = total + m2
	#end for i
	return 1.0*total/len(numList)
#end fun 
	
#Length overlap in loop region
def getLengthOfOverlapInLoop( miRNASeq, RNASequence, RNAStructure):
	t1 = getDistanceFromTerminalLoop(miRNASeq, RNASequence, RNAStructure)
	if( t1 < 0 ):
		return -1.0*t1
	else:
		return 0
#end fun

#Bulge at specific position around the start of miRNA, 0: False; 1:True
def getBulgeAtSpecificPosition_Start (miRNA, RNASequence, RNAStructure, offset):
	[miRNAStartPos, miRNAEndPos] = getMiRNAPosition( miRNA, RNASequence )
	spPos = miRNAStartPos + offset
	if( spPos < 0 or spPos > len(RNAStructure)-1 ):
		return 0
	else:
		ch = RNAStructure[spPos]
		if( ch == '.' ):
			return 1
		else:
			return 0
	#end else
#end fun 

#Bulge at end position around the end of miRNA. 0:False; 1:True
def getBulgeAtSpecificPosition_End (miRNASeq, RNASequence, RNAStructure, offset):
	[miRNAStartPos, miRNAEndPos]  = getMiRNAPosition( miRNASeq, RNASequence )
	spPos = miRNAEndPos + offset
	if( spPos < 0 or spPos >= len(RNAStructure)-1 ):
		return 0
	else:
		ch = RNAStructure[spPos]
		if( ch == '.' ):
			return 1
		else:
			return 0
	#end else
#end fun 


#number of bulges in miRNA
def getNumberOfBulges( miRNASeq, RNASequence, RNAStructure ):
	miRNAStruct = getMiRNAStructure (miRNASeq, RNASequence, RNAStructure )
	num = 0
	for i in range(len(miRNAStruct)-2):
		ch1 = miRNAStruct[i]
		ch2 = miRNAStruct[i+1]
		if( ch1 == '.' and isParenthese(ch2) ):
			num = num + 1 
	#end for i
	return num
#end fun

##get dinucleotide content
def getDiNucleotideContent( miRNASeq, ch1, ch2 ):
	subStr = ch1 + ch2
	m = miRNASeq.count( subStr )
	res = 1.0*m/len(miRNASeq)
	return res
#end fun

def getAllDiNucleotideContent( miRNASeq ):
	chs = ["A", "C", "G", "U"]
	res = []
	for i in range(len(chs)):
		ch1 = chs[i]
		for j in range(len(chs)):
			ch2 = chs[j]
			res.append( getDiNucleotideContent( miRNASeq, ch1, ch2 ) )
		#end for j 
	#end for i
	return res
#end fun 
			
##get mono nucleotide
def getMonoNucleotideContent (miRNASeq, ch):
	m = miRNASeq.count(ch)
	return 1.0*m/len(miRNASeq)
#end fun
	
##get all mono nucleotide 
def getAllMonoNucleotideContent( miRNASeq ):
	ContA = getMonoNucleotideContent( miRNASeq, "A")
	ContC = getMonoNucleotideContent( miRNASeq, "C")
	ContG = getMonoNucleotideContent( miRNASeq, "G")
	ContU = getMonoNucleotideContent( miRNASeq, "U")
	return [ContA, ContC, ContG, ContU]
#end fun 

def getDiSeqStructure(miRNASeq, RNASequence, RNAStructure ):
	miRNAStruct = getMiRNAStructure (miRNASeq, RNASequence, RNAStructure )
	chars = ["A", "C", "G", "U"]
	dots = ["(", ".", ")"]
	resDic = {}
	for i in range(len(chars)):
		for j in range(len(chars)):
			for x in range(len(dots)):
				for y in range(len(dots)):
					curKey = chars[i] + chars[j] + dots[x] + dots[y]
					resDic[curKey] = 0
	#end for i
	resDic["others"] = 0
	
	for i in range(1, len(miRNASeq)):
		ch1 = miRNASeq[i-1]
		ch2 = miRNASeq[i]
		dot1 = miRNAStruct[i-1]
		dot2 = miRNAStruct[i]
		curKey = ch1 + ch2 + dot1 + dot2
		if( curKey in resDic.keys() ):
			resDic[curKey] = resDic[curKey] + 1
		else:
			resDic["others"] = resDic["others"] + 1
	#end for i

	#sort keys
	allKeys = sorted( resDic.keys() )
	res = []
	for curKey in allKeys:
		res.append( 1.0*resDic[curKey]/len(miRNASeq) )
	#end for curKey
	return res
#end fun 

	

##get all triplets
def getAllTriplets(miRNASeq, RNASequence, RNAStructure ):
	miRNAStruct = getMiRNAStructure (miRNASeq, RNASequence, RNAStructure )
	resDic = {"A...":0,"C...":0,"G...":0,"U...":0,"A(..":0,"C(..":0,"G(..":0,"U(..":0,"A((.":0,"C((.":0,"G((.":0,"U((.":0,"A.((":0,"C.((":0,"G.((":0,"U.((":0,"A(((":0,"C(((":0,"G(((":0,"U(((":0,"A.(.":0,"C.(.":0,"G.(.":0,"U.(.":0,"A..(":0,"C..(":0,"G..(":0,"U..(":0,"A(.(":0,"C(.(":0,"G(.(":0,"U(.(":0,"other":0}
	for i in range(1,len(miRNASeq)-2):
		curKey = miRNASeq[i] + miRNAStruct[i-1:i+2]
		if curKey in resDic.keys():
			resDic[curKey] = resDic[curKey] + 1
		else:
			resDic["other"] = resDic["other"] + 1
	#end for i
	
	#sort keys
	allKeys = sorted( resDic.keys() )
	res = []
	for curKey in allKeys:
		res.append( 1.0*resDic[curKey]/len(miRNASeq) )
	#end for curKey

	return res
#end fun

##get all mono-Nucleotide&Structure
def getMonoSeqStructure( miRNASeq, RNASequence, RNAStructure ):
	miRNAStruct = getMiRNAStructure (miRNASeq, RNASequence, RNAStructure )
	miRNALen = getMiRNALen( miRNASeq )
	resDic = {"A.":0, "A(":0,"A)":0,"C.":0, "C(":0,"C)":0,"G.":0, "G(":0,"G)":0,"U.":0, "U(":0,"U)":0, "others":0}
	for i in range(miRNALen):
		curKey = miRNASeq[i] + miRNAStruct[i]
		if( curKey in resDic.keys() ):
			resDic[curKey] = resDic[curKey] + 1
		else:
			resDic["others"] = resDic["others"] + 1
	#end for i

	#sort keys
	allKeys = sorted( resDic.keys() )
	res = []
	for curKey in allKeys:
		res.append( 1.0*resDic[curKey]/miRNALen )
	#end for curKey
	return res
#end fun


##decoding *_dp.ps file for get positional Entropy
def getPositionalEntropy( dpPSFile, RNASequence ):
	
	length = len(RNASequence)
	mm = {}
	mp = {}
	pp = {}
	sp = {}
	p0 = {}
	for i in range(0, length+1):
		mm[i] = 0.0
		mp[i] = 0.0
		pp[i] = 0.0
		sp[i] = 0.0
		p0[i] = 0.0
	#end for i 
	
	max = 0.0
	lines = readLinesFromFile(dpPSFile)
	flag = 0
	for i in range(len(lines)):
		curLine = lines[i]
		if( "%start of base pair probability data" in curLine ):
			flag = 1
			continue
		if( "showpage" in curLine ):
			flag = 0
		if( flag != 1):
			continue
		curLine = curLine.strip()
		[posi, posj, prob, boxType] = curLine.split(" ")
		#print posi, posj, prob, boxType, length
		posi = int(posi)
		posj = int(posj)
		prob = float(prob)
		if( boxType == "ubox" ):
			#square prob to probability
			prob = prob*prob
			ss = 0
			if( prob > 0 ):
				ss = prob*math.log(prob)
			
			mp[posi + 1] = mp[posi+1] + prob
			mp[posj] = mp[posj] - prob
			
			sp[posi] = sp[posi] + ss
			sp[posj] = sp[posj] + ss
			pp[posi] = pp[posi] + prob
			pp[posj] = pp[posj] + prob
		elif( boxType == "lbox" ):
			mm[posi+1] = mm[posi+1] + 1
			mm[posj] = mm[posj] - 1
		#end if 
	#end for i 
	
	mp[0] = 0
	mm[0] = 0
	max = 0
	posProb = []
	posMFE = []
	posEntropy = []
	for i in range(1,length+1):
		mp[i] = mp[i] + mp[i-1]
		if( mp[i] > max ):
			max = mp[i]
		mm[i] = mm[i] + mm[i-1]
		sp[i] = sp[i] + (1-pp[i])*math.log(1-pp[i])
		
		tmp = -1.0*sp[i]/math.log(2)
		posEntropy.append( tmp )
		
		posProb.append( mp[i] )
		posMFE.append( mm[i] )
	#end for i 
	
	return [posProb, posMFE, posEntropy]
#end fun


#get positional entropies around a specific positions.
def getPosEntropyAtSpecificPos ( posEntropy, position, w, l ):
	upList = []
	downList = []
	p1 = position - w
	p2 = position + l + 1
	if( p1 < 0 ):
		upList = [posEntropy[0]]*abs(p1)
		p1 = 0
		
	if( p2 > len(posEntropy) ):
		downList = [posEntropy[-1]]*abs(p2 - len(posEntropy))
		p2 = len(posEntropy)
	
	res = upList + posEntropy[p1:p2] + downList
	#print w+l+1, position, p1, p2, len(posEntropy), len(upList), len(posEntropy[p1:p2]), len(downList), len(res)
	return res
#end fun 	
		

##get RNA structure and positional base-pair probability, and positial entropy
def getRNAStructureInfo ( RNASequence, RNAFoldDic, tempFileDir ):
	fpw = open(tempFileDir, "w")
	fpw.write( ">seq\n" + RNASequence + "\n" )
	fpw.close()
	
	resultFileDir = tempFileDir + "_res"
	
	osType = checkOSType()
	dpPSFile = ""
	order = ""
	if( osType == "win" ):
		order = RNAFoldDic + "RNAfold.exe -p --noLP < " + tempFileDir + " > " +  resultFileDir
		dpPSFile = RNAFoldDic + "seq_dp.ps"
	elif( osType == "linux" ):
		order = RNAFoldDic + "RNAfold -p --noLP < " + tempFileDir + " > " +  resultFileDir
		dpPSFile = ""
	else:
		sys.exit("Error: undefined OS")
	#end if 
	#print order
	res = os.system( order )
	if( res != 0 ):
		print "Error to run order:", order
		sys.exit()
	#end if 
	

	##get structure info
	lines = readLinesFromFile( resultFileDir )
	StructureLine = lines[2]
	[Structure, Energy] = StructureLine.split( " " )
	#removeFile(resultFileDir)
	
	##positional entropy
	resList = getPositionalEntropy( dpPSFile, RNASequence )
	posProb = resList[0]
	posMFE = resList[1]
	posEntropy = resList[2]
	
	resList = {"sequence":RNASequence, "structure":Structure, "energy":Energy, "posProb":posProb, "posMFE":posMFE, "posEntropy":posEntropy}
	return resList
#end fun


def getPosEntropyForAllSequences (miRBaseFileDir, RNAFolderDic, resultDic):
	
	allSeq = readSequenceAndStructure(miRBaseFileDir)
	seqNum = len(allSeq)
	
	resultDir_Seq = resultDic + "00_allSeq.txt"
	resultDir_Struct = resultDic + "00_allStruct.txt"
	fpw = open(resultDir_Seq, "w")
	for i in range(seqNum):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		fpw.write( ">" + curMiRNAID + "\n" + curPreMiRNASeq + "\n" )
	#end for i 
	fpw.close()
	
	##run RNAfolder
	osType = checkOSType()
	order = ""
	if( osType == "win" ):
		order = RNAFolderDic + "RNAfold.exe -p --noLP < " + resultDir_Seq + " > " +  resultDir_Struct
	elif( osType == "linux" ):
		order = RNAFolderDic + "RNAfold -p --noLP < " + resultDir_Seq + " > " +  resultDir_Struct
	else:
		sys.exit("Error: undefined OS")
	#end if 

	
	res = os.system( order )
	if( res != 0 ):
		print "Error to run order:", order
		sys.exit()
	#end if 
#end fun

#code nucleotide type
def codeNucleotide( ch ):
	dist = {"A":[0,0,0,1], "C":[0,0,1,0], "G":[0,1,0,0], "U":[1,0,0,0], "a":[0,0,0,1], "c":[0,0,1,0], "g":[0,1,0,0], "u":[1,0,0,0]}
	#dist = {"A":[1], "C":[2], "G":[3], "U":[4], "a":[1], "c":[2], "g":[3], "u":[4]}
	if( ch in "ACGUacgu" ):
		return dist[ch]
	else:
		return dist["A"]
#end fun 

##get nucleotide type at specific position
def codeNucleotideForPosition( RNASequence, Position):
	pos = Position
	if( pos < 0 ):
		pos = 0
	if( pos > len(RNASequence) - 1 ):
		pos = len(RNASequence) - 1
	ch = RNASequence[pos]
	return( codeNucleotide(ch) )
#end fun 

#code dinucleotide type
def codeDiNucleotide(ch1, ch2):
	dist = {"AA":[1], "AC":[2], "AG":[3], "AU":[4], "CA":[5], "CC":[6], "CG":[7], "CU":[8], "GA":[9], "GC":[10], "GG":[11], "GU":[12], "UA":[13], "UC":[14], "UG":[15], "UU":[16]}
	ch = ch1 + ch2 
	if( ch in dist.keys() ):
		return dist[ch]
	else:
		print ch, "not in codeDiNucleotide"
		return dist["AA"]
#end fun 

#get nucleotide type at specific position
def codeDiNucleotideForPosition( RNASequence, Position1, Position2 ):
	
	RNASeqLen = len(RNASequence)
	pos1 = Position1
	pos2 = Position2

	if( pos1 < 0 ):
		pos1 = 0
	if( pos2 < 0 ):
		pos2 = 1
	if( pos1 > RNASeqLen - 1):
		pos1 = RNASeqLen - 2
	if( pos2 > RNASeqLen - 1):
		pos2 = RNASeqLen - 1
	return ( codeDiNucleotide(RNASequence[pos1], RNASequence[pos2]) )
#end fun 

def codeDiNucleotideForPosition_up_down( RNASequence, Position, up, down ):
	offsetList = range(-1*up, down+1)
	resList = []
	for curOffset in offsetList:
		resList = resList + codeNucleotideForPosition( RNASequence, Position + curOffset )
	return resList
#end def 

##get sample index for cross validation
def cross_validation_sample_index( sampleNum, cv = 10 ):
	x = np.arange(sampleNum)
	random.shuffle(x)
	cvlist = np.array_split(x, cv)
	return cvlist
#end fun 

##get cv samples 
def cross_validation_round_i ( cvSampleList, Round_i, allSeq, resultDic ):
	trainFile = resultDic + "cv_" + str(Round_i) + "_trainSamples.txt"
	testFile = resultDic + "cv_" + str(Round_i) + "_testSamples.txt"
	fpw_train = open(trainFile, "w")
	fpw_test = open( testFile, "w")
	for i in range(len(cvSampleList) ):
		curCVSampleList = cvSampleList[i]
		if( i == Round_i ):
			#samples for test 
			for j in curCVSampleList:
				[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[j]
				fpw_test.write( curMiRNAID + "\t" + curPreMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n")
			#end for j
		else:
			for j in curCVSampleList:
				[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[j]
				fpw_train.write( curMiRNAID + "\t" + curPreMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n")
			#end for j
		#end if
	#end for i
	fpw_train.close()
	fpw_test.close()
	return [trainFile, testFile]
#end fun


##code RNA sequences
def deCodingMiRNASequence (miRNASequence, miRNAType, RNASequence, RNAStructure, RNAPosEntropy, RNAFoldDic, tempFileDir, MFEDic, matchedStructList = [], upOffLen = 5, downOffLen = 5 ):
	
	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure( RNAStructure )
	
	#1st feature:miRNA length
	miRNALen = getMiRNALen( miRNASequence )
	#2nd feature: miRNA GCContent
	miRNAGC = getGCContent( miRNASequence )

	#3-6 feature: content of mono nucleotide 
	MonoNucleotideContent = getAllMonoNucleotideContent( miRNASequence )

	#7-22 features: dinucleotide content 
	DiNucleotideContent = getAllDiNucleotideContent( miRNASequence )

	#miRNA star 
	miRNAStarSeq = getMiRNAStar( RNASequence, RNAStructure, miRNASequence, matchedStructList  )
	[miRNAStarStartPos, miRNAStarEndPos] = getMiRNAPosition( miRNAStarSeq, miRNASequence )
	csMiRNASeq = computeComplementaritySequence(RNASequence, RNAStructure, miRNASequence, matchedStructList)
	
	
	#23rd feature: MFE
	MFE = 0
	if( miRNASequence not in MFEDic.keys() ):
		MFE = calculateMFE( miRNASequence, csMiRNASeq, RNAFoldDic, tempFileDir )
	else:
		MFE = MFEDic[miRNASequence]
	
	#get miRNA structure
	miRNAStruct = getMiRNAStructure( miRNASequence, RNASequence, RNAStructure )

	#feature: maximal length of miRNA without bulge
	mlBulge = getMaximumLengthWithoutBulges( miRNAStruct )

	#feature: percenate of maximal length of miRNA without bulge
	mlBulge_Perct = getMaximumLengthWithoutBulgesPerc( miRNAStruct )

	#feature: number of base pairs in miRNA and miRNA* duplex
	bpNum = getBasePairsInDuplex( miRNAStruct )

	#feautre:distance to the terminal loop 
	dist2loop = getDistanceFromTerminalLoop( miRNASequence, RNASequence, RNAStructure )

	#feature: distance to the start of helix
	dist2Helix = getDistanceFromHairpinStart( miRNASequence, RNASequence, RNAStructure )

	#feature: number of bases in loop 
	numInLoop = getLengthOfOverlapInLoop( miRNASequence, RNASequence, RNAStructure )

	#1 feature: number of bulges in miRNA sequence
	numBulges = getNumberOfBulges( miRNASequence, RNASequence, RNAStructure )


	start_20Mer = getStartOfPerfect20MerBasePair(miRNAStruct)
	persent_20Mer = getPresenceOfPerfect20MerBasePair(miRNAStruct)
	start_10Mer = getStartOfPerfect10MerBasePair(miRNAStruct)
	persent_10Mer = getPresenceOfPerfect10MerBasePair(miRNAStruct)
	start_5Mer = getStartOfPerfect5MerBasePair(miRNAStruct)
	persent_5Mer = getPresenceOfPerfect5MerBasePair(miRNAStruct)

	NumBP_Win7 = getAverageNumberOfBasePairInWindow( miRNAStruct, 7 )
	NumBP_Win5 = getAverageNumberOfBasePairInWindow( miRNAStruct, 5 )
	NumBP_Win3 = getAverageNumberOfBasePairInWindow( miRNAStruct, 3 )


	#feature: bulge at specific position around the start of miRNA sequence 
	BulgeAtStart_u3 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, -3)
	BulgeAtStart_u2 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, -2)
	BulgeAtStart_u1 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, -1)
	BulgeAtStart_0	= getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, 0)
	BulgeAtStart_d1 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, 1)
	BulgeAtStart_d2 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, 2)
	BulgeAtStart_d3 = getBulgeAtSpecificPosition_Start (miRNASequence, RNASequence, RNAStructure, 3)

	#feature: bulge at specific position around the end of miRNA sequence 
	BulgeAtEnd_u3 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, -3)
	BulgeAtEnd_u2 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, -2)
	BulgeAtEnd_u1 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, -1)
	BulgeAtEnd_0  = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, 0)
	BulgeAtEnd_d1 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, 1)
	BulgeAtEnd_d2 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, 2)
	BulgeAtEnd_d3 = getBulgeAtSpecificPosition_End (miRNASequence, RNASequence, RNAStructure, 3)

	#12 features: mono-nucleotide & strucutre features
	MonoSeqStructFeatures = getMonoSeqStructure( miRNASequence, RNASequence, RNAStructure )

	# features: di-nucleotide and structure features
	DiSeqStructFeatures = getDiSeqStructure( miRNASequence, RNASequence, RNAStructure )

	#33 features: triplets sequence & strucutre features
	tripleSeqStructFeatures = getAllTriplets(miRNASequence, RNASequence, RNAStructure )


	#19*2 features: positional entropy features
	[miRNAStartPos, miRNAEndPos] = getMiRNAPosition( miRNASequence, RNASequence )
	upPosEntropy = getPosEntropyAtSpecificPos ( RNAPosEntropy, miRNAStartPos, upOffLen, downOffLen )
	downPosEntropy = getPosEntropyAtSpecificPos ( RNAPosEntropy, miRNAEndPos, upOffLen, downOffLen )

	#nucleotide type at position around the start and end of miRNA sequence
	NtStart = codeDiNucleotideForPosition_up_down( RNASequence, miRNAStartPos, upOffLen, downOffLen )
	NtEnd =  codeDiNucleotideForPosition_up_down( RNASequence, miRNAEndPos, upOffLen, downOffLen )
	NtList = NtStart + NtEnd

	#for miRNA start, region around the starts and ends.
	NtStart1 = codeDiNucleotideForPosition_up_down( RNASequence, miRNAStarStartPos, upOffLen, downOffLen )
	NtEnd1 = codeDiNucleotideForPosition_up_down( RNASequence, miRNAStarEndPos, upOffLen, downOffLen )
	NtList_miRNAStar = NtStart1 + NtEnd1
	
	#combine all features, ok, keep it.
	res = [miRNAType, miRNALen, miRNAGC, MFE, mlBulge, bpNum, dist2loop, dist2Helix, numInLoop, numBulges, start_20Mer, persent_20Mer, start_10Mer, persent_10Mer,start_5Mer, persent_5Mer, NumBP_Win7, NumBP_Win5, NumBP_Win3] + MonoNucleotideContent + DiNucleotideContent + [BulgeAtStart_u3, BulgeAtStart_u2, BulgeAtStart_u1, BulgeAtStart_0, BulgeAtStart_d1, BulgeAtStart_d2, BulgeAtStart_d3, BulgeAtEnd_u3, BulgeAtEnd_u2, BulgeAtEnd_u1, BulgeAtEnd_0, BulgeAtEnd_d1, BulgeAtEnd_d2, BulgeAtEnd_d3] + MonoSeqStructFeatures + DiSeqStructFeatures + tripleSeqStructFeatures + upPosEntropy + downPosEntropy + NtList + NtList_miRNAStar

	return res
#end fun 


##get miRNA sequence 
def getMiRNASequence( RNASequence, miRNAPos, miRNALen ):
	if( miRNAPos + miRNALen > len(RNASequence) ):
		sys.exit("Error: the End position of miRNA is too large.")
	return RNASequence[ miRNAPos:(miRNAPos + miRNALen) ]
#end fun 



def negativeSampleSelection( trueMiRNASeq, RNASequence, RNAStructure,  matchedStructList = [] ):
	[trueMiRNAStartPos, trueMiRNAEndPos] = getMiRNAPosition(trueMiRNASeq, RNASequence )
	trueMiRNALen = len(trueMiRNASeq)
	
	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure(RNAStructure)

	#check Arm
	trueArmType = checkArm( RNASequence, RNAStructure, trueMiRNASeq )

	posList = []
	for i in range(len(RNASequence) - trueMiRNALen - 1):
		if( math.fabs( i - trueMiRNAStartPos) <= 5 ):
			continue
		curMiRNASeq = getMiRNASequence( RNASequence, i, trueMiRNALen )
		curArmType = checkArm( RNASequence, RNAStructure, curMiRNASeq )
		########################################################
		#if( curArmType != "arm5" and curArmType != "arm3" ):
		#	continue
		if( curArmType != "arm5" ):
			continue
		
		miRNAStarSeq = getMiRNAStar( RNASequence, RNAStructure, curMiRNASeq, matchedStructList )
		if( len( miRNAStarSeq ) > 30 ):
			continue
		if( miRNAStarSeq.count('N') > 0 ):
			continue
		posList.append(i)
	#end for i
	
	negativeMiRNASeq = ""
	randomPos = 0
	if( len(posList) > 0 ):
		randomNum = randint( 0, len(posList)-1 )
		randomPos = posList[randomNum]
		negativeMiRNASeq = getMiRNASequence( RNASequence, randomPos, trueMiRNALen)
	return negativeMiRNASeq
#end fun 



##generate validation file 
def generateValidationFile( allSeq, validateSampleFileDir, validateSampleLabelFileDir ):
	fpw = open( validateSampleFileDir, "w")
	fpw_label = open( validateSampleLabelFileDir, "w")
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		matchedStructList = matchRNAStructure( curPreMiRNAStructure )
		curNegativeSample = negativeSampleSelection( curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure, matchedStructList )
		if( len(curNegativeSample) == 0 ):
			continue
		fpw.write( curMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n" )
		fpw.write( curMiRNAID+"_neg" + "\t" + curNegativeSample + "\t" + curPreMiRNASeq + "\t" +  curPreMiRNAStructure + "\n" )
		fpw_label.write( "1\n0\n")
	#end for i
	fpw.close()
	fpw_label.close()
#end fun 


def generatePredictionFile( allSeq, predSampleFileDir, predSampleAnnotFileDir ):
	fpw = open( predSampleFileDir, "w")
	fpw_Annot = open( predSampleAnnotFileDir, "w")
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		matchedStructList = matchRNAStructure( curPreMiRNAStructure )
		#curNegativeSample = negativeSampleSelection( curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure, matchedStructList )
		#if( len(curNegativeSample) == 0 ):
		#	continue
		fpw.write( curMiRNAID + "\t" + curPreMiRNASeq + "\n" )
		fpw_Annot.write( curMiRNAID+"_neg" + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" +  curPreMiRNAStructure + "\n" )
	#end for i
	fpw.close()
	fpw_Annot.close()
#end fun 

def getDPPSFileDir ( dpSSFileDic, curMiRNAID ):
	
	#print "Teeeest", dpSSFileDic, curMiRNAID
	dpPSFile = dpSSFileDic + curMiRNAID + "_dp.ps"
	if( fileExist( dpPSFile ) ):
		return dpPSFile
	
	dpPSFile = dpSSFileDic + curMiRNAID + "-5p_dp.ps"
	if( fileExist( dpPSFile ) ):
		return dpPSFile
		
	dpPSFile = dpSSFileDic + curMiRNAID + "-3p_dp.ps"
	if( fileExist( dpPSFile ) ):
		return dpPSFile
		
	idx = curMiRNAID.rfind("-")
	dpPSFile = dpSSFileDic + curMiRNAID[:idx] + "_dp.ps"
	if( fileExist( dpPSFile ) ):
		return dpPSFile
		
	return "NotFind"
#end def



def calcuateMFEForMiRNADuplex( RNACandidateList, RNAFoldDic, tempFileDir ):
	fpw = open( tempFileDir, "w")
	for i in range(len(RNACandidateList) ):
		[curMiRNASeq, curMiRNAStarSeq] = RNACandidateList[i]
		fpw.write( ">candidate" + str(i) + "\n" + curMiRNASeq + "\n" + ">candidateStar" + str(i) + "\n" + curMiRNAStarSeq + "\n" )
	#end for i

	RNAduplexResFile = tempFileDir + "_RNAduplex"
	order = RNAFoldDic + "RNAduplex < " + tempFileDir + " > " + RNAduplexResFile
	res = os.system( order )
	if( res != 0 ):
		print "Error to run RNAduplex for calculating MFE for miRNASeq"
		sys.exit()
	#end if 
	

	MFEDic = {}
	num = 0
	lines = readLinesFromFile( RNAduplexResFile )
	for curLine in lines:
		if( len(curLine) == 0 ):
			continue
		if( curLine[0] == '>' ):
			continue
		curLine = curLine.strip()
		items = curLine.split("(")
		lastItem = items[-1]
		MFE = lastItem.replace(")", "")
		[curMiRNASeq, curMiRNAStarSeq] = RNACandidateList[num]
		MFEDic[curMiRNASeq] = MFE
		num = num + 1
	#end for 

	removeFile( tempFileDir )
	removeFile(RNAduplexResFile)
	return MFEDic
#end fun 

##generate candidate miRNAs for one pre-miRNA sequence 
def generateCandidateMiRNAs( preMiRNASeq, preMiRNAStructure, minCandidateMiRNALen, maxCandidateMiRNALen, candidateMiRNAName, candidateMiRNAFileDir ):
	fpw = open( candidateMiRNAFileDir, "w")
	for curMiRNALen in range(minCandidateMiRNALen,maxCandidateMiRNALen+1):
		for curMiRNAPos in range(0, len(preMiRNASeq) - curMiRNALen):
			curMiRNASeq = preMiRNASeq[curMiRNAPos:curMiRNAPos+curMiRNALen]
			##arm check
			armType = checkArm( preMiRNASeq, preMiRNAStructure, curMiRNASeq )
			if( armType == "arm3" ):
				break
			curMiRNAID = candidateMiRNAName + "_" + str(curMiRNAPos) + "_" + str(curMiRNALen)
			fpw.write( curMiRNAID + "\t" + curMiRNASeq + "\t" + preMiRNASeq + "\t" + preMiRNAStructure + "\n")
		#end for 
	#end curMiRNALen
	fpw.close()
#end fun



##extract all miRNA info 
def getAllMiRNAInfo( miRNA_Seq_Struct_FileDir ):
	allMiRNAInfo = []
	lineList = readLinesFromFile( miRNA_Seq_Struct_FileDir )
	for curLine in lineList:
		curLine = curLine.strip("\n")
		if( len(curLine) == 0 ):
		  continue
		[curMiRNAID, curMiRNASeq, preMiRNASeq, preMiRNAStructure] = curLine.split("\t")
		[curMiRNAStartPos, curMiRNAEndPos] = getMiRNAPosition( curMiRNASeq, preMiRNASeq )
		curMiRNALen = getMiRNALen( curMiRNASeq )
		curMiRNAInfo = [curMiRNAID, curMiRNAStartPos, curMiRNALen, curMiRNASeq]
		allMiRNAInfo.append(curMiRNAInfo)
	#end for 
	return allMiRNAInfo
#end fun 
 

##generate features for sequences to be test 
def codePredictedSequence( RNASequence, RNAStructure, RNAPosEntropy, RNAFoldDic, tempFileDir, candidateMiRNAFileDir, matchedStructList = [], upOffSet = 5, downOffSet = 5 ):

	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure(RNAStructure)
		
	##read all candidate MiRNAs
	lineList = readLinesFromFile( candidateMiRNAFileDir )
	miRNACandidateList = []
	for curLine in lineList:
		[curMiRNAID, curMiRNASeq, preMiRNASeq, preMiRNAStructure] = curLine.split("\t")
		curMiRNAStarSeq = getMiRNAStar( preMiRNASeq, preMiRNAStructure, curMiRNASeq, matchedStructList )
		miRNACandidateList.append( [curMiRNASeq, curMiRNAStarSeq] )
	#end for 

	##get MFE for these RNA duplex 
	MFEDic = calcuateMFEForMiRNADuplex( miRNACandidateList, RNAFoldDic, tempFileDir )
	
	##generate feature list 
	allFeatureList = []
	for i in range( len(miRNACandidateList)):
		[curMiRNASeq, curMiRNAStarSeq] = miRNACandidateList[i]
		curFeatureList = deCodingMiRNASequence (curMiRNASeq, "0", RNASequence, RNAStructure, RNAPosEntropy, RNAFoldDic, tempFileDir, MFEDic, matchedStructList, upOffSet, downOffSet )
		allFeatureList.append( curFeatureList )
	#end fur curMiRNALen
	return allFeatureList
#end fun 


##get index of sorted feature importance 
def getIndexForTopImportantFeatures( importanceScores, N ):
	sortedList = sorted( importanceScores, reverse = True )
	scoreThreshold = sortedList[N-1]
	idx = []
	for i in range(len(importanceScores)):
		if( importanceScores[i] >= scoreThreshold):
			idx.append(i)
	#end for i
	return idx 
#end fun 



##write 2d-List
def output2DList(list2d, FileDir ):
	fpw = open( FileDir, "w")
	for i in range(len(list2d)):
		curList = list2d[i]
		for j in range(len(curList) ):
			fpw.write(  str(curList[j]) )
			if( j < len(curList) - 1 ):
				fpw.write( "\t")
			else:
				fpw.write( "\n")
		#end for j
	#end for i
	fpw.close()
#end fun 

##initialize 2d array 
def Init2dArray( nrow, ncol, value ):
	tt = [x[:] for x in [[value]*ncol]*nrow]
	return tt
#end fun
 
##for trained prediction model      
def trainPredModel( allFeatureList ):

	##transform 2dlist to 2darray
	featureArray = transform_list_2_array( allFeatureList )
	x = featureArray[0::,1::]
	y = featureArray[0::,0]
	model = RandomForestClassifier( n_estimators = 200, criterion = 'gini'  )
	model = model.fit(x,y)	
	return model
#end def



##save prediction model from sklearn
def savePredModel( predModel, fileDir ):
	_ = joblib.dump(predModel, fileDir, compress=9)
#end fun

##load prediction model
def loadPredModel( predModelFileDir ):
	predModel = joblib.load(predModelFileDir)
	return predModel
#end fun 



##decoding all RNA sequences for generating feature matrix
def deCodingAllSequences_ForTrain (allSeq, dpSSFileDic, RNAFoldDic, tempFileDir, upOffSet, downOffSet):

	featureMat = []
	posNum = 0
	negNum = 0
	for i in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
		matchedStructList = matchRNAStructure( curPreMiRNAStructure )
		
		dpPSFile = getDPPSFileDir( dpSSFileDic,  curPreMiRNAID )
		[curPosProb, curPosMFE, curPosEntropy] = getPositionalEntropy( dpPSFile, curPreMiRNASeq )

		#arm checkArm
		armType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq)
		
		#get miRNA star
		curMiRNAStarSeq = getMiRNAStar( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq, matchedStructList )
		#check miRNA star len
		if( len(curMiRNAStarSeq) > 30 ):
			continue

		#For true miRNA
		#print "for true miRNA", curMiRNASeq
		MFEDic = {}
		curSampleFeatures = deCodingMiRNASequence (curMiRNASeq, 1, curPreMiRNASeq, curPreMiRNAStructure, curPosEntropy, RNAFoldDic, tempFileDir, MFEDic, matchedStructList, upOffSet, downOffSet )
		
		featureMat.append(curSampleFeatures)
		#featureMat.append(curSampleFeatures + [curMiRNAID, armType, "pos"])
		posNum = posNum + 1
		

		#for negative miRNA 
		curNegMiRNASeq = negativeSampleSelection( curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure, matchedStructList )
		curNegMiRNAarmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curNegMiRNASeq)
		if( len(curNegMiRNASeq) == 0 ):
			continue
		#print "for negative sample", curNegMiRNASeq
		curSampleFeatures = deCodingMiRNASequence (curNegMiRNASeq, 0, curPreMiRNASeq, curPreMiRNAStructure, curPosEntropy, RNAFoldDic, tempFileDir, MFEDic, matchedStructList, upOffSet, downOffSet )
		featureMat.append(curSampleFeatures)
		#featureMat.append(curSampleFeatures + [curMiRNAID, curNegMiRNAarmType, "neg"])
		negNum = negNum + 1
		#print "finish", curMiRNAID
	#end for i
	print "In training dataset, positives:", posNum, "negatives:", negNum
	return featureMat
#end fun


#generate cross validation for machine learning
def generateCrossValidationFile_2015( cv, allSeq, resultDic ):
	preMiRNADic = {}
	for ii in range(len(allSeq)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[ii]
		if( curPreMiRNAID not in preMiRNADic.keys() ):
			preMiRNADic[curPreMiRNAID] = [allSeq[ii]]
		else:
			tmp = preMiRNADic[curPreMiRNAID]
			tmp.append( allSeq[ii] )
			preMiRNADic[curPreMiRNAID] = tmp
		#end else
	#end for ii

	##sample randomization
	sampleIDs = preMiRNADic.keys()
	x = np.arange(len(sampleIDs))
	random.shuffle(x)
	cvSampleList = np.array_split(x, cv)
	print "Total pri-miRNAs:", len(sampleIDs)

	#generate training and testing files for each round of cross validation
	for Round_i in range(len(cvSampleList)):
		trainFile = resultDic + "cv_" + str(Round_i) + "_trainSamples.txt"
		testFile = resultDic + "cv_" + str(Round_i) + "_testSamples.txt"
		print trainFile
		fpw_train = open(trainFile, "w")
		fpw_test = open( testFile, "w")
		curCVSampleList_Test = cvSampleList[Round_i]
		for kk in range(len(sampleIDs)):
			curSampleID = sampleIDs[kk]
			annotInfo = preMiRNADic[curSampleID]
			for xx in range(len(annotInfo) ):
				[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = annotInfo[xx]
				if( kk in curCVSampleList_Test ):
					fpw_test.write( curMiRNAID + "\t" + curPreMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n")
				else:
					fpw_train.write( curMiRNAID + "\t" + curPreMiRNAID + "\t" + curMiRNASeq + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\n")
				#end else
			#end for xx
		#end for kk
		fpw_train.close()
		fpw_test.close()
	#end for Round_i
#end def

def collaspe2PreMiRNA( allSeq ):
  preMiRNADic = {}
  for i in range(len(allSeq) ):
    [curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
    if( curPreMiRNAID not in preMiRNADic.keys() ):
      preMiRNADic[curPreMiRNAID] = [curPreMiRNAID, curPreMiRNASeq, curPreMiRNAStructure]
  #end for
#end def
  



def cross_validation_function( cv, trainDataFileDir, minCandidateMiRNALen, maxCandidateMiRNALen, upOffSet, downOffSet, minPredScore, cvResultDic, dpSSFileDic, RNAFoldDic, tempFileDir ):
  
	#load all sequences and structures
	allSeq0 = readSequenceAndStructure(trainDataFileDir)
	#remove miRNAs in loop regions. We didnit consider miRNAs in loop regions at this version of miRLocator
	allSeq1 = removeMiRNAInLoop( allSeq0 )

	#remove pre-miRNAs carrying mutiple miRNAs on one arm
	allSeq2 = removeMultipleMiRNAsOneArm( allSeq1 )
	allSeq = allSeq2
	
	saveSeq2File(allSeq2, cvResultDic + "all_miRNAs_for_cross_validation.txt" )

	generateCrossValidationFile_2015( cv, allSeq, cvResultDic )

	print "start cross validation"
	for i in range(cv):
		#generate train and test miRNAs for cross validation
		trainFileDir = cvResultDic + "cv_" + str(i) + "_trainSamples.txt"
		testFileDir = cvResultDic + "cv_" + str(i) + "_testSamples.txt"
		#record training samples
		allSeq_train = readSequenceAndStructure(trainFileDir)
		print "cv_", i, len(allSeq_train), "miRNAs used for training"
		#record testing samples
		allSeq_test = readSequenceAndStructure(testFileDir)
		print "cv_", i, len(allSeq_test), " tested sequences"
	
		###########################train RFMiRNA######################################
		allSeq_train_refined = refinePreMiRNASeq( allSeq_train )
		allSeq_train_armTransform = armTransform( allSeq_train_refined )
		allFeatureList = deCodingAllSequences_ForTrain (allSeq_train_armTransform, dpSSFileDic, RNAFoldDic, tempFileDir, upOffSet, downOffSet )
		trainedModel = trainPredModel( allFeatureList )
		
		##save prediction
		trainedModelFileDir = cvResultDic + "cv_" + str(i) + "_trainPredictedModel" 
		savePredModel( trainedModel, trainedModelFileDir )

		##load trained prediction model
		#trainedModel = loadPredModel(trainedModelFileDir)
		#for prediction model 
		predResultDir = cvResultDic + "cv_" + str(i) + "_testing_AllPredMiRNAs.txt"
		fpw = open( predResultDir, "w" )
		print "cv_", i, len(allSeq_test), " tested sequences"
		
		##from miRNAs to pre-miRNAs
		allSeq_test = refinePreMiRNASeq(allSeq_test)
		for j in range(len(allSeq_test)):
			[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq_test[j]
			matchedStructList = matchRNAStructure( curPreMiRNAStructure )

			#generate positional entropy
			dpPSFile = getDPPSFileDir( dpSSFileDic, curPreMiRNAID ) #20141227
			[curPosProb, curPosMFE, curRNAPosEntropy] = getPositionalEntropy( dpPSFile, curPreMiRNASeq )

			#generate candidate miRNAs
			candidateMiRNAFileDir = cvResultDic + curPreMiRNAID + "_allCandiateMiRNAs.txt"
			#if( fileExist(candidateMiRNAFileDir) == False ):
			generateCandidateMiRNAs( curPreMiRNASeq, curPreMiRNAStructure, minCandidateMiRNALen, maxCandidateMiRNALen, curPreMiRNAID, candidateMiRNAFileDir )
			allMiRNAInfo = getAllMiRNAInfo( candidateMiRNAFileDir )

			#generate feature list for all candidate miRNAs and prediction scores
			allFeatureList = codePredictedSequence( curPreMiRNASeq, curPreMiRNAStructure, curRNAPosEntropy, RNAFoldDic, tempFileDir, candidateMiRNAFileDir, matchedStructList, upOffSet, downOffSet )
			allPredScores = predScores_2015( allFeatureList, trainedModel )

			#format prediction scores and allMiRNAinfo
			predScoreFileDir = cvResultDic + curPreMiRNAID + "_mlMiRNA_PredScore.txt"
			[predMiRNAPos, predMiRNALen] = formatPredictScoreAcrossPreMiRNA_2015( allMiRNAInfo, allPredScores, curPreMiRNASeq, curPreMiRNAStructure, predScoreFileDir, matchedStructList, minPredScore )
			curPredMiRNASeq = curPreMiRNASeq[predMiRNAPos:predMiRNAPos+predMiRNALen]
			curPredMiRNAStarSeq = getMiRNAStar( curPreMiRNASeq, curPreMiRNAStructure, curPredMiRNASeq, matchedStructList )
			fpw.write( curPreMiRNAID + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\t" + curPredMiRNASeq + "(5')" + "\t" + curPredMiRNAStarSeq + "(3')" + "\n")
	
			##remove generated candidate miRNAs
			removeFile( candidateMiRNAFileDir )
			removeFile( predScoreFileDir )
			#######################################################################
		##end for j
		fpw.close()
		
		##evaluation
		evalResultDir = cvResultDic + "cv_" + str(i) + "_evalResult.txt"
		eval_dif_resolutions( testFileDir, predResultDir, evalResultDir )
	#end for i
	
#	print "Successfully to run cross validation"
#	fileFlag = "_testing_AllPredMiRNAs.txt"
#	statFileDir = cvResultDic + "00_miRNALocator_cv_StatResult.txt"
#	miRdupResultList = eval_cv_results( allSeq, cv, cvResultDic, fileFlag, statFileDir, outputFlag = 1 )

	print "Successfully to run cross validation!"
#end fun 

##training model with miRNAs in one file
def train_prediction_model( trainDataFileDir, dpSSFileDic, RNAFoldDic, tempFileDir, upOffSet, downOffSet, trainedModelFileDir, resultDic ):
  #load all sequences and structures
  allSeq0 = readSequenceAndStructure(trainDataFileDir)
  #remove miRNAs in loop regions. We didnit consider miRNAs in loop regions at this version of miRLocator
  allSeq1 = removeMiRNAInLoop( allSeq0 )

  #remove pre-miRNAs carrying mutiple miRNAs on one arm
  allSeq2 = removeMultipleMiRNAsOneArm( allSeq1 )
  
  allSeq_train_refined = refinePreMiRNASeq( allSeq2 )
  saveSeq2File(allSeq_train_refined, resultDic + "all_miRNAs_for_training.txt" )
   
  allSeq_train_armTransform = armTransform( allSeq_train_refined )
  allFeatureList = deCodingAllSequences_ForTrain (allSeq_train_armTransform, dpSSFileDic, RNAFoldDic, tempFileDir, upOffSet, downOffSet )
  trainedModel = trainPredModel( allFeatureList )
  savePredModel( trainedModel, trainedModelFileDir )
  return trainedModel
#end fun


##prediction 
def prediction( predictionDataFileDir, dpSSFileDic, RNAFoldDic, tempFileDir, minCandidateMiRNALen, maxCandidateMiRNALen, upOffSet, downOffSet, minPredScore, trainedModel, resultFileDir ):
  lines = readLinesFromFile(predictionDataFileDir)
  fpw = open( resultFileDir, "w" )
  
  for curLine in lines:
    curLine = curLine.strip('\n')
    [curPreMiRNAID, curPreMiRNASeq, curPreMiRNAStructure] = curLine.split("\t")
    #print "predicting...", curPreMiRNAID, curPreMiRNASeq, curPreMiRNAStructure
    matchedStructList = matchRNAStructure( curPreMiRNAStructure )

    #generate positional entropy
    dpPSFile = getDPPSFileDir( dpSSFileDic, curPreMiRNAID ) #20141227
    [curPosProb, curPosMFE, curRNAPosEntropy] = getPositionalEntropy( dpPSFile, curPreMiRNASeq )

    #generate candidate miRNAs
    candidateMiRNAFileDir = resultFileDir + "_allCandiateMiRNAs.txt"   
    generateCandidateMiRNAs( curPreMiRNASeq, curPreMiRNAStructure, minCandidateMiRNALen, maxCandidateMiRNALen, curPreMiRNAID, candidateMiRNAFileDir )
    allMiRNAInfo = getAllMiRNAInfo( candidateMiRNAFileDir )

    #generate feature list for all candidate miRNAs and prediction scores
    allFeatureList = codePredictedSequence( curPreMiRNASeq, curPreMiRNAStructure, curRNAPosEntropy, RNAFoldDic, tempFileDir, candidateMiRNAFileDir, matchedStructList, upOffSet, downOffSet )
    allPredScores = predScores_2015( allFeatureList, trainedModel )

    #format prediction scores and allMiRNAinfo
    predScoreFileDir = resultFileDir + "_mlMiRNA_PredScore.txt"
    [predMiRNAPos, predMiRNALen] = formatPredictScoreAcrossPreMiRNA_2015( allMiRNAInfo, allPredScores, curPreMiRNASeq, curPreMiRNAStructure, predScoreFileDir, matchedStructList, minPredScore )
    curPredMiRNASeq = curPreMiRNASeq[predMiRNAPos:predMiRNAPos+predMiRNALen]
    curPredMiRNAStarSeq = getMiRNAStar( curPreMiRNASeq, curPreMiRNAStructure, curPredMiRNASeq, matchedStructList )
    fpw.write( curPreMiRNAID + "\t" + curPreMiRNASeq + "\t" + curPreMiRNAStructure + "\t" + curPredMiRNASeq + "(5')" + "\t" + curPredMiRNAStarSeq + "(3')" + "\n")
	
    ##remove generated candidate miRNAs
    removeFile( candidateMiRNAFileDir )
    removeFile( predScoreFileDir )
  #end for curLine
  fpw.close()
#end def
  
  
  
  
  
  
  

##format predicted Score
def formatPredictScoreAcrossPreMiRNA_2015( allMiRNAInfo, allPredScores, TruePreMiRNASeq, TruePreMiRNAStructure, predScoreFileDir, matchedStructList, minPredScore ):
	
	if( len(matchedStructList) == 0 ):
		matchedStructList = matchRNAStructure(TruePreMiRNAStructure)

	maxMiRNAStart = 0
	miRNALenList = []
	for i in range( len(allMiRNAInfo) ):
		[curMiRNAID, curMiRNAPos, curMiRNALen, curMiRNASeq] = allMiRNAInfo[i]
		if( maxMiRNAStart < curMiRNAPos):
			maxMiRNAStart = curMiRNAPos
		miRNALenList.append( curMiRNALen )
	#end for i
	
	miRNALenList = list( set(miRNALenList) )
	resDic = {}
	for curMiRNALen in miRNALenList:
		resDic[curMiRNALen] = [0]*(maxMiRNAStart+1)
	#end for
	#print "!!!!", maxMiRNAStart

	#for pred miRNA	
	tmpMiRNAID = ""
	for i in range( len(allMiRNAInfo) ):
		[curMiRNAID, curMiRNAPos, curMiRNALen, curMiRNASeq] = allMiRNAInfo[i]			
		tmp = resDic[curMiRNALen]
		#print "!!!!", curMiRNAPos, len(tmp), allPredScores[i]
		tmp[curMiRNAPos] =  allPredScores[i]
		resDic[curMiRNALen] = tmp
	#end for i
	
	#print resDic, TTTTTTT
	fpw = open( predScoreFileDir, "w")
	for curKey in resDic.keys():
		tmp = resDic[curKey]
		fpw.write( str(curKey) )
		for j in range(len(tmp)):
			fpw.write( "\t" + str(tmp[j]) )
		fpw.write( "\n" )
	#end for 
	fpw.close()
	

	#print "Heree", resDic.keys()
	predScoreList = []
	for curKey in resDic.keys():
		tmp = resDic[curKey]
		tmp = [curKey] + tmp 
		predScoreList.append( tmp )
	#end curKey 
	
	#print predScoreList

	#find the predicted miRNA 
	predScorePosDic = resDic
	#print predScorePosDic


	[candidateMiRNAPos, candidateMiRNALen ] = findCandidateMiRNA_2014 (predScorePosDic, minPredScore )
	#print "True:", TrueMiRNAStart, "..", TrueMiRNAStart + TrueMiRNALen, "Pred:", candidateMiRNAPos, "..", candidateMiRNAPos + candidateMiRNALen
	
	return [candidateMiRNAPos, candidateMiRNALen ]
#end fun


##find the most possible miRNA on a RNA sequence , 0.90 is ok
def findCandidateMiRNA_2014 (predScorePosDic, threshold = 0.00 ):
	candidateLens = sorted(predScorePosDic.keys() )

	#construct a 2d array 
	nrow = len(candidateLens)
	ncol = len( predScorePosDic[ candidateLens[0] ] )
	scoreMat = Init2dArray( nrow, ncol, 0.0 )

	for i in range(nrow):
		curScores = predScorePosDic[ candidateLens[i] ]
		for j in range(ncol):
			scoreMat[i][j] = curScores[j]
		#end for j
	#end for i
	
	##for position-specific sumScore
	#for start scores 
	sumScores = [0]*ncol
	for j in range(ncol):
		curScore = 0
		for i in range(nrow):
			curScore = curScore + scoreMat[i][j]
		#end for i
		sumScores[j] = curScore
	#end for j
	
	#find max SumScore
	maxSumScore = 0
	maxSumScoreIdx = np.argmax(sumScores)
	
	##OK, get start position of predicted miRNA
	maxScore_MiRNAStartPos = maxSumScoreIdx
	if( isinstance( maxScore_MiRNAStartPos, list) ):
		maxScore_MiRNAStartPos = maxScore_MiRNAStartPos[0]
	
	#get prediction scores for different miRNAs from maxSumScoreIdx
	predScoreDiffLen = [0.0]*nrow
	for i in range(nrow):
		predScoreDiffLen[i] = scoreMat[i][maxScore_MiRNAStartPos ]
	#end for i
	
	maxScoreDiffLen = max(predScoreDiffLen)
	selLen = []
	for i in range(nrow):
		if( predScoreDiffLen[i] >= maxScoreDiffLen ):
			selLen.append( candidateLens[i] )
	#end for i
	
	#get averaged selLen
	meanLen = np.mean(selLen)
	
	##get the final predicted miRNA length
	maxScore_MiRNALen = int(meanLen)
	
	return [maxScore_MiRNAStartPos, maxScore_MiRNALen ]
#end fun 




##load all predicted miRNAs
def load_predictResults( resultFileDir ):
	
	resultDic = {}
	
	lineList = readLinesFromFile( resultFileDir )
	for curLine in lineList:
		curLine = curLine.strip()
		tmpList = curLine.split("	")
		[curMiRNAID, curPreMiRNASeq, curPreMiRNAStructure] = tmpList[0:3]
		curMiRNA1 = curMiRNA2 = ""
		#print curMiRNAID, curPreMiRNASeq, "\n", curPreMiRNAStructure
		predMiRNA5Start = predMiRNA5End = predMiRNA3Start = predMiRNA3End = 0
		if( "no predictable miRNA" not in curLine ):
			[curMiRNA1, curMiRNA2] = tmpList[-2:]
			[curMiRNA1, miRNALoc] = curMiRNA1.split("(")
			[curMiRNA2, miRNALoc] = curMiRNA2.split("(")
			#print curMiRNA1, "\n", curMiRNA2
			[predMiRNAStart1, predMiRNAEnd1] = getMiRNAPosition( curMiRNA1, curPreMiRNASeq )
			[predMiRNAStart2, predMiRNAEnd2] = getMiRNAPosition( curMiRNA2, curPreMiRNASeq )
				
			if( predMiRNAStart1 < predMiRNAStart2 ):
				predMiRNA5Start = predMiRNAStart1
				predMiRNA5End = predMiRNA5Start + getMiRNALen(curMiRNA1)
				predMiRNA3Start = predMiRNAStart2
				predMiRNA3End = predMiRNA3Start + getMiRNALen(curMiRNA2)
			else:
				predMiRNA5Start = predMiRNAStart2
				predMiRNA5End = predMiRNA5Start + getMiRNALen(curMiRNA2)
				predMiRNA3Start = predMiRNAStart1
				predMiRNA3End = predMiRNA3Start + getMiRNALen(curMiRNA1)				

			
		resultDic[curMiRNAID] = [curMiRNAID, curPreMiRNASeq, curPreMiRNAStructure, predMiRNA5Start, predMiRNA5End, predMiRNA3Start, predMiRNA3End]
	#end for curLine
	return 	resultDic
#end fun



##load all predicted miRNAs
def load_cv_predict_results( cv, cvResDic, fileFlag ):
	
	resultDic = {}
	
	for i in range(cv):
		curCVPredRes = load_predictResults( cvResDic + "cv_" + str(i) + fileFlag )
		resultDic = dict(resultDic.items() + curCVPredRes.items())
	#end for i
	return 	resultDic
#end fun

##select prediction scores for a given class 
def selectPredScores ( allPredScores, classTypes, spClass ):
	spClassIdx = 0
	for i in range(len(classTypes)):
		if( classTypes[i] == spClass ):
			spClassIdx = i
	#end for i

	spPredScores = []
	for i in range(len(allPredScores)):
		tmp = allPredScores[i]
		spPredScores.append( tmp[spClassIdx])
	#end for i
	return spPredScores
#end for

#20150204
##evaluate prediction results at different resolutions
def eval_dif_resolutions( realMiRNAFileDir, predMiRNAFileDir, resultFileDir = "" ):
  
      #load prediction results, each pre-miRNA per line
      predDic = load_predictResults( predMiRNAFileDir )
        
      #for the annotation of testing miRNAs, each miRNA per line  
      allSeq = readSequenceAndStructure(realMiRNAFileDir)
  
      #transfer list to dictionary
      sampleDic = {}
      for i in range(len(allSeq)):
	[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq[i]
	sampleDic[curMiRNAID] = allSeq[i]
      #end for i
      
      ##compare annoated and predicted miRNAs
      failedPredNum = 0
      allInfoList = []
      for curKey in sampleDic.keys():
	#for annotation info
	[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = sampleDic[curKey]
	[annotMiRNAStart, annotMiRNAEnd] = getMiRNAPosition( curMiRNASeq, curPreMiRNASeq )
	annotMiRNALen = getMiRNALen( curMiRNASeq )
	annotArmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
	
	#for prediction info
	if( curPreMiRNAID not in predDic ):
	  print "No prediction in", curPreMiRNAID, ", please check reasons"
	  sys.exit()
	[curMiRNAID_p, curPreMiRNASeq_p, curPreMiRNAStructure_p, predMiRNA5Start, predMiRNA5End, predMiRNA3Start, predMiRNA3End] = predDic[curPreMiRNAID]
	if( predMiRNA5Start == predMiRNA5End or predMiRNA3Start == predMiRNA3End ):
	  failedPredNum = failedPredNum + 1
		
	tmp = sampleDic[curKey]
	if( annotArmType == "arm3" ):
		tmp = tmp + ["cv"+str(i), str(annotMiRNAStart), str(annotMiRNAStart + annotMiRNALen), str(predMiRNA3Start), str(predMiRNA3End), str(predMiRNA3Start - annotMiRNAStart), str(predMiRNA3End - (annotMiRNAStart + annotMiRNALen)) ]
	else:
		tmp = tmp + ["cv"+str(i), str(annotMiRNAStart), str(annotMiRNAStart + annotMiRNALen), str(predMiRNA5Start), str(predMiRNA5End), str(predMiRNA5Start - annotMiRNAStart), str(predMiRNA5End - (annotMiRNAStart + annotMiRNALen)) ]
	allInfoList.append(tmp)	
      #end for curKey

      ##stat
      deltaDist_StartPos = [0]*31
      deltaDist_EndPos = [0]*31
      for i in range(len(allInfoList) ):
		tmp = allInfoList[i]
		[curDeltaStart, curDeltaEnd] = tmp[-2:]
		p1 = abs(int(curDeltaStart))
		p2 = abs(int(curDeltaEnd))
		if( p1 <= 30 ):
			deltaDist_StartPos[p1] = deltaDist_StartPos[p1] + 1
		if( p2 <= 30 ):
			deltaDist_EndPos[p2] = deltaDist_EndPos[p2] + 1
      #cum
      #print deltaDist_StartPos, "\n", deltaDist_EndPos
      for i in range(1, len(deltaDist_StartPos)):
		deltaDist_StartPos[i] = deltaDist_StartPos[i] + deltaDist_StartPos[i-1]	
		deltaDist_EndPos[i] = deltaDist_EndPos[i] + deltaDist_EndPos[i-1]
      #end for 
	
	
      #percentage
      allSeqNum = len(allInfoList)
      for i in range(0, len(deltaDist_StartPos)):
		deltaDist_StartPos[i] = 1.0*deltaDist_StartPos[i]/allSeqNum
		deltaDist_EndPos[i] = 1.0*deltaDist_EndPos[i]/allSeqNum
		print "deltaDist:", i, "Start:", round(deltaDist_StartPos[i],3), "End:", round(deltaDist_EndPos[i],3)
      #end for 
      
      
      #output
      if( len(resultFileDir) > 1 ):
	#append
	with open (resultFileDir, "a") as fpw:
	  for i in range(0, len(deltaDist_StartPos)):
	    fpw.write( "DelaDistance\t" + str(i) + "\tstart\t" + str(round(deltaDist_StartPos[i],3)) + "\tEnd\t" + str( round(deltaDist_EndPos[i],3)) + "\n" )
	  #end for 
	fpw.close()
      #end if
	
      return [deltaDist_StartPos, deltaDist_EndPos]
#end fun
  
  

##evaluation for miRNAdup
def eval_cv_results( allSeq, cv, cvResDic, fileFlag, statFileDir, outputFlag = 1 ):
	
	##first refine all seq
	allSeq_Refined = refinePreMiRNASeq( allSeq )
	
	#transfer list to dictionary
	sampleDic = {}
	for i in range(len(allSeq_Refined)):
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = allSeq_Refined[i]
		sampleDic[curMiRNAID] = allSeq_Refined[i]
	#end for i
	
	##load predicted miRNAs
	predDic = load_cv_predict_results( cv, cvResDic, fileFlag )
	
	##compare annoated and predicted miRNAs
	failedPredNum = 0
	allInfoList = []
	for curKey in sampleDic.keys():
		#for annotation info
		[curMiRNAID, curPreMiRNAID, curMiRNASeq, curPreMiRNASeq, curPreMiRNAStructure] = sampleDic[curKey]
		[annotMiRNAStart, annotMiRNAEnd] = getMiRNAPosition( curMiRNASeq, curPreMiRNASeq )
		annotMiRNALen = getMiRNALen( curMiRNASeq )
		annotArmType = checkArm( curPreMiRNASeq, curPreMiRNAStructure, curMiRNASeq )
		
		#for prediction info
		if( curKey not in predDic ):
			print curMiRNAID, "not included in predictions, please check reasons"
			sys.exit()
		[curMiRNAID_p, curPreMiRNASeq_p, curPreMiRNAStructure_p, predMiRNA5Start, predMiRNA5End, predMiRNA3Start, predMiRNA3End] = predDic[curKey]
		if( predMiRNA5Start == predMiRNA5End or predMiRNA3Start == predMiRNA3End ):
			failedPredNum = failedPredNum + 1
		
		tmp = sampleDic[curKey]
		if( annotArmType == "arm3" ):
			tmp = tmp + ["cv"+str(i), str(annotMiRNAStart), str(annotMiRNAStart + annotMiRNALen), str(predMiRNA3Start), str(predMiRNA3End), str(predMiRNA3Start - annotMiRNAStart), str(predMiRNA3End - (annotMiRNAStart + annotMiRNALen)) ]
		else:
			tmp = tmp + ["cv"+str(i), str(annotMiRNAStart), str(annotMiRNAStart + annotMiRNALen), str(predMiRNA5Start), str(predMiRNA5End), str(predMiRNA5Start - annotMiRNAStart), str(predMiRNA5End - (annotMiRNAStart + annotMiRNALen)) ]
		allInfoList.append(tmp)	
	#end for curKey
	print "\n\n============================================================="
	print failedPredNum, " pre-miRNAs unsuccessfully predicted"

	##stat
	deltaDist_StartPos = [0]*31
	deltaDist_EndPos = [0]*31
	for i in range(len(allInfoList) ):
		tmp = allInfoList[i]
		[curDeltaStart, curDeltaEnd] = tmp[-2:]
		p1 = abs(int(curDeltaStart))
		p2 = abs(int(curDeltaEnd))
		if( p1 <= 30 ):
			deltaDist_StartPos[p1] = deltaDist_StartPos[p1] + 1
		if( p2 <= 30 ):
			deltaDist_EndPos[p2] = deltaDist_EndPos[p2] + 1
	#cum
	#print deltaDist_StartPos, "\n", deltaDist_EndPos
	for i in range(1, len(deltaDist_StartPos)):
		deltaDist_StartPos[i] = deltaDist_StartPos[i] + deltaDist_StartPos[i-1]	
		deltaDist_EndPos[i] = deltaDist_EndPos[i] + deltaDist_EndPos[i-1]
	#end for 
	
	
	#percentage
	allSeqNum = len(allInfoList)
	for i in range(0, len(deltaDist_StartPos)):
		deltaDist_StartPos[i] = 1.0*deltaDist_StartPos[i]/allSeqNum
		deltaDist_EndPos[i] = 1.0*deltaDist_EndPos[i]/allSeqNum
		print "deltaDist:", i, "Start:", round(deltaDist_StartPos[i],3), "End:", round(deltaDist_EndPos[i],3)
	#end for 
	print "all results for ", allSeqNum, " miRNAs"


	if( outputFlag == 1 ):
		resultDir = cvResDic + "01_DeltaDist" + fileFlag
		#output2DList(allInfoList, resultDir )
		
		#append
		with open (resultDir, "a") as fpw:
			for i in range(0, len(deltaDist_StartPos)):
				fpw.write( "DelaDistance\t" + str(i) + "\tstart\t" + str(round(deltaDist_StartPos[i],3)) + "\tEnd\t" + str( round(deltaDist_EndPos[i],3)) + "\n" )
		fpw.close()
		
		lineList = readLinesFromFile( resultDir )
		writeLinesToFile( lineList, "", statFileDir )
		removeFile( resultDir )

	return allInfoList
#end fun 



##pred scores for multiple samples 
def predScores_2015( allFeatureList, trainedModel ):
	featureArray = transform_list_2_array( allFeatureList )
	x = featureArray[0::,1::]
	y = featureArray[0::,0]
	model = trainedModel
	classTypes = model.classes_
	lastPredScores = selectPredScores ( model.predict_proba(x), classTypes, '1' )
	return 	lastPredScores
#end fun

  
  
  
 


  


