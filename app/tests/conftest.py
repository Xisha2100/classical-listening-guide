import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))
from backend.scores import build_score
from backend.store import Store

# Pickup, rest, chord, triplet, tie crossing a bar, Bb transposition, repeat, tempo change.
SCORE=b'''<?xml version="1.0"?><score-partwise version="4.0"><part-list><score-part id="P1"><part-name>Clarinet</part-name></score-part></part-list><part id="P1">
<measure number="0" implicit="yes"><attributes><divisions>6</divisions><key><fifths>0</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef><transpose><diatonic>-1</diatonic><chromatic>-2</chromatic></transpose></attributes><direction><sound tempo="60"/></direction><note><rest/><duration>3</duration><type>eighth</type></note><note><pitch><step>A</step><octave>4</octave></pitch><duration>3</duration><type>eighth</type></note></measure>
<measure number="1"><note><pitch><step>C</step><octave>5</octave></pitch><duration>6</duration><type>quarter</type></note><note><chord/><pitch><step>E</step><octave>5</octave></pitch><duration>6</duration><type>quarter</type></note><note><pitch><step>D</step><octave>5</octave></pitch><duration>2</duration><type>eighth</type><time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification><notations><tuplet type="start" number="1"/></notations></note><note><pitch><step>E</step><octave>5</octave></pitch><duration>2</duration><type>eighth</type><time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification></note><note><pitch><step>F</step><octave>5</octave></pitch><duration>2</duration><type>eighth</type><time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification><notations><tuplet type="stop" number="1"/></notations></note><note><pitch><step>G</step><octave>5</octave></pitch><duration>12</duration><tie type="start"/><type>half</type><notations><tied type="start"/></notations></note></measure>
<measure number="2"><direction><sound tempo="120"/></direction><note><pitch><step>G</step><octave>5</octave></pitch><duration>6</duration><tie type="stop"/><type>quarter</type><notations><tied type="stop"/></notations></note><note><rest/><duration>18</duration><type>half</type><dot/></note><barline location="right"><repeat direction="backward"/></barline></measure></part></score-partwise>'''

@pytest.fixture
def score(tmp_path):
 version,index=build_score(SCORE,tmp_path/'generated')
 return tmp_path/'generated'/version,index

@pytest.fixture
def store(tmp_path,score):
 import shutil
 path,index=score
 s=Store(tmp_path/'library')
 shutil.copytree(path,s.assets/'generated'/'test-work'/index['version'])
 s.put_work({'id':'test-work','title':'测试作品','aliases':['贝五'],'composer':'测试作者','catalogue':'Op.67','movement':'第一乐章','score_version':index['version']})
 return s
