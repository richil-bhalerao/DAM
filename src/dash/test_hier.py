'''
Created on Jun 12, 2013

@author: richilb
'''



import hier

from hier import Hier

H = Hier()

# Test 1: checks the manager of user
if  H.manager("alex") == 'hmprabhu':        
    print 'test for manager("alex") passed'
else:
    print 'test for manager("alex") failed'
    
# Test 2: checks a list of all reports    
if H.reports("lmandic", 0) == sorted(['aassadza', 'cdahm', 'kpagadala', 'ksivaraj', 'mfong', 'tbirajdar', 'tkekan', 'vkpatel', 'yishijima', 'rboileau', 'emacneil', 'etempest', 'hshanmugam', 'hstewart', 'jethridge', 'knasim', 'lbazinet', 'mqiao', 'pchen', 'ppieda', 'vasanth', 'wangh', 'rgovindarajan', 'aranpise', 'bpalaniswami', 'bselbrede', 'cna', 'manang', 'pcomstock', 'ptaravind', 'sbhagwath', 'venukonda', 'vsriram', 'angelat', 'deo', 'dmitrym', 'dvdgray', 'jessicah', 'jestin', 'jvanhorne', 'klash', 'kraj', 'ravindg', 'trix', 'tyreddy', 'ehunter', 'abstine', 'amandshahi', 'anjali', 'groeck', 'jsurya', 'marcelm', 'mguglani', 'anshukla', 'aronen', 'gvdl', 'jelliott', 'jkai', 'kshrikanth', 'sdmishra', 'stevek', 'tvenkata', 'pnh', 'pramod', 'ragreddy', 'ylu', 'gheorghiu', 'abarakat', 'andyle', 'carlos', 'chinh', 'ekelly', 'hiepd', 'hyan', 'jkojo', 'kazotsuka', 'kokorelis', 'kuljinder', 'mckiernan', 'mhaluza', 'barak', 'bhan', 'akroy', 'amitk', 'kartheek', 'manikandan', 'manojkumar', 'mprabhu', 'nbudoor', 'pjude', 'raghup', 'rohitj', 'amsuls', 'arjun', 'devaraj', 'kalin', 'madhusr', 'maheshkg', 'malleshi', 'nravi', 'sathikk', 'srim', 'stephend', 'gvrengan', 'ilavarasu', 'ksathish', 'kumark', 'nanmathi', 'praju', 'ranjithas', 'rrajesh', 'sabarishk', 'sendilk', 'vjanand', 'sambiger', 'vigneshwaran', 'shripad', 'sureshjd', 'velur', 'gigiguo', 'bobfan', 'henryyin', 'leanli', 'mattma', 'xinli', 'grose', 'jay', 'daman', 'bharper', 'cangus', 'cclarke', 'dlloyd', 'dougt', 'torekolee', 'estrada', 'kriss', 'acorstorphine', 'amarans', 'bjames', 'dannyt', 'dmcdowell', 'kbasi', 'ksandhu', 'mresngit', 'pgarcia', 'rharwood', 'vmathiya', 'kdubray', 'lchai', 'rwells', 'hpurewal', 'jarmstrong', 'klloyd', 'nickp', 'vjohnican', 'sbottcher', 'aouldsfiya', 'damurray', 'etwine', 'galopez', 'jpmurray', 'rlmartin', 'jmolinari', 'mlopez', 'tbaltimore', 'highstreet', 'dalebrown', 'bning', 'davidchen', 'derafshan', 'eovadia', 'aantony', 'allenyu', 'clotito', 'dsreddy', 'gchavan', 'gstovall', 'igaikwad', 'mbasha', 'mgodi', 'mshivanna', 'msrivastav', 'ndivya', 'phanin', 'richilb', 'rkunwor', 'sdsouza', 'sgodbole', 'smulyono', 'jkatinsky', 'hmprabhu', 'alex', 'hnswamy', 'ajsingh', 'bmontoya', 'deeptil', 'dtripathi', 'jeffchen', 'kishorbs', 'kniranjan', 'krajagopal', 'krvenk', 'ksharma', 'mgokhale', 'rajesha', 'ravikp', 'scmohan', 'shameer', 'skarisala', 'spaku', 'mayankr', 'ranjit', 'akashm', 'lsandip', 'pawan', 'poonams', 'rdash', 'ssammiti', 'suris', 'vhiremath', 'vishalgupta', 'siddalingesh', 'syrajendra', 'vinreddy', 'dhavnoor', 'mmazur', 'smithal', 'ssagar', 'bbanerje', 'biyer', 'ibarker', 'praveenm', 'smedanci', 'tapplegate', 'tpham', 'tquilici', 'wambold', 'daveu', 'dwolf', 'justinb', 'nraja', 'ssiano', 'tp', 'zzhao', 'kjain', 'avinod', 'amitarora', 'bkumara', 'chandru', 'jana', 'ktabrez', 'manojnayak', 'nabil', 'psarathi', 'rgumasta', 'rkdavid', 'shyamk', 'srinivds', 'viveka', 'vsudharsan', 'satishd', 'amitrao', 'bhargav', 'cpraveen', 'dvsingh', 'jithing', 'kmunna', 'mavj', 'rbadiger', 'rejithomas', 'rkrishan', 'rvivek', 'saurabg', 'silambu', 'sjindal', 'svashisht', 'tanmoyk', 'saurabhm', 'amitg', 'anandmr', 'anupraoy', 'avink', 'cskumar', 'gauravg', 'kprash', 'ksukesh', 'roraveen', 'srushtigs', 'sseth', 'swarns', 'shivayenigalla', 'abishek', 'harmeets', 'manirk', 'nsairam', 'prashr', 'singhpra', 'subram', 'vpasikanti', 'pallavi', 'arunmr', 'hant', 'amgowano', 'atchandra', 'dchuang', 'gbhavani', 'knilangekar', 'mdsouza', 'nmichraf', 'rcheh', 'rjohnst', 'sksubra', 'hlakshmi', 'jschulman', 'oansari', 'bivanic', 'anupamas', 'bdinh', 'jgiorgis', 'jsding', 'kwu', 'nguyenc', 'nnishiya', 'pingli', 'yfang', 'emccolgan', 'charliel', 'eolson', 'lovan', 'pwisdom', 'rdonle', 'wasim', 'jammyc', 'kenjim', 'qhao', 'rjnaroth', 'rocker', 'sbattu', 'jhayes', 'uchandra', 'psen', 'gkarthi', 'kaleem', 'kmani', 'msumit', 'nithyaram', 'shree', 'ssathya', 'sundararajk', 'tapanswain', 'victord', 'anishl', 'awadhn', 'bhavya', 'ddash', 'ksmanoj', 'nivethar', 'pmullapudi', 'rkishore', 'smithashan', 'sreenig', 'sweekark', 'vui', 'phil', 'pushpavally', 'rameshrn', 'adimulam', 'dhilipkr', 'jurid', 'ksanjay', 'lokeswarab', 'mchandra', 'nsimaria', 'rsankar', 'subodh', 'aanbarasan', 'ajaykc', 'ankitj', 'arus', 'asifa', 'balasank', 'dsatya', 'dtrivedi', 'ericv', 'ganeshvs', 'gnalawade', 'katharh', 'ktiwari', 'pkumarpr', 'ramas', 'ravikv', 'sgoudar', 'somasm', 'svitta', 'abhinavt', 'bijchand', 'mvivek', 'rnaren', 'svivek', 'tchittar', 'rpiyush', 'agovinde', 'akhiljha', 'arajagopal', 'babum', 'hrajendran', 'karthikeyan', 'lekshmin', 'poojag', 'ppalani', 'rajuk', 'rushabhs', 'sahubars', 'sarathg', 'surengr', 'arunad', 'ashishks', 'beena', 'ahiriadaka', 'akjha', 'jayaganesh', 'karthia', 'mwasif', 'prathapcv', 'ravisankar', 'rmaiya', 'sateeshk', 'sundarkh', 'vikashc', 'vivk', 'ckevin', 'djadhav', 'ksacca', 'amychen', 'aprabakaran', 'dlau', 'dsolis', 'htseng', 'ilum', 'jblock', 'joline', 'kpacunas', 'moina', 'slau', 'tcliu', 'mvenu', 'anildkum', 'athangaraj', 'ayuvaraj', 'cviswana', 'ihazra', 'mgsreenath', 'srimadhav', 'ssamanth', 'narayanbt', 'aarul', 'kfathima', 'manojn', 'rafikp', 'thilagavathyp', 'tvranga', 'rajis', 'sindhujha', 'smondal', 'srreddy', 'aparnar', 'aramamurthy', 'ashweta', 'asish', 'chipujar', 'eers', 'gvenkata', 'jnanesh', 'jyothin', 'kaverib', 'kevinr', 'nsonali', 'ramtsb', 'rdevulapalli', 'santoshm', 'shanbhag', 'sraju', 'vinaykants', 'sumangala', 'apreethi', 'arula', 'arunr', 'ashag', 'chandraiahp', 'karneys', 'kkalyani', 'kmeka', 'krishnar', 'lajadas', 'lohithab', 'mamallan', 'mpavan', 'msakamuri', 'pravnara', 'priyab', 'prkaruna', 'pseenivasagam', 'rajasi', 'rksathish', 'rmanju', 'rreddy', 'sathish', 'sibis', 'skmohan', 'spagadal', 'sraghavendr', 'sravilla', 'ssinduja', 'sumati', 'thangap', 'trajkumar', 'vijaygadde', 'viswanathn', 'vpendela', 'wgriffeth', 'wing', 'setember', 'seth', 'amesh', 'chitrad', 'dcc', 'gerd', 'janem', 'jduncan', 'kavi', 'mdb', 'siv', 'tlarock', 'sjg', 'thiraoka', 'akalaiah', 'austinlee', 'biddyc', 'dqiao', 'kiruba', 'leccese', 'mbiswal', 'rsunkoji', 'vikastr', 'yqiu', 'dfalak', 'jshaw', 'minchenet', 'mjsharma', 'mmitchell', 'nshook', 'rakurati', 'sjeffries', 'sonalk', 'viveksingh', 'vsatish'], key=str.lower):  
    print 'test for reports("lmandic", 0) passed'
else:
    print 'test for reports("lmandic", 0) failed'
    
# Test 3: checks a list of only immmediate reports
if H.reports("lmandic", 1) == sorted(['aassadza', 'angelat', 'ehunter', 'gheorghiu', 'highstreet', 'kjain', 'pallavi', 'setember', 'seth', 'sjg', 'thiraoka'], key=str.lower):  
    print 'test for reports("lmandic", 1) passed'
else:
    print 'test for reports("lmandic", 1) failed'
    
# Test 4: checks a list of immediate managers under username specified
if H.managers("lmandic", 1) == sorted(['aassadza', 'angelat', 'ehunter', 'gheorghiu', 'highstreet', 'kjain', 'pallavi', 'seth', 'thiraoka'], key=str.lower): 
    print 'test for managers("lmandic", 1) passed'
else:
    print 'test for managers("lmandic", 1) failed'
    
# Test 5: gives a list of all managers under username specified
if H.managers("lmandic", 0) == sorted(['aassadza', 'cdahm', 'rboileau', 'rgovindarajan', 'angelat', 'ehunter', 'mguglani', 'gheorghiu', 'abarakat', 'bhan', 'rohitj', 'arjun', 'ilavarasu', 'gigiguo', 'jay', 'daman', 'kriss', 'rwells', 'sbottcher', 'rlmartin', 'highstreet', 'dalebrown', 'derafshan', 'eovadia', 'hmprabhu', 'hnswamy', 'ranjit', 'vinreddy', 'ssagar', 'wambold', 'kjain', 'avinod', 'satishd', 'saurabhm', 'shivayenigalla', 'pallavi', 'hant', 'oansari', 'bivanic', 'emccolgan', 'jammyc', 'uchandra', 'psen', 'victord', 'rameshrn', 'subodh', 'svitta', 'rpiyush', 'arajagopal', 'beena', 'ksacca', 'mvenu', 'narayanbt', 'srreddy', 'sumangala', 'seth', 'thiraoka', 'austinlee'], key=str.lower): 
    print 'test for managers("lmandic", 0) passed'
else:
    print 'test for managers("lmandic", 0) failed'
    
# Test 6: checks a listing of all employees who are unmanaged
if H.unmanaged() == sorted(['achandak', 'achou', 'agnelom', 'andrey.bondarenko@kaspersky.com', 'andrey.sploshnov@kaspersky.com', 'andreyk', 'ashankar', 'asultan', 'brutberg', 'cdbu-tools', 'chrishwang', 'cmbu-qa', 'cmengel', 'cpetrucelli@trivenidigital.com', 'craskar', 'czanpure', 'daniell@radware.com', 'dc-test-cp', 'dc-test-fc', 'dc-test-platform', 'ddavari', 'ddos-secure-customer-escalation-pr-owner', 'ddos-secure-software-dev-pr-owner', 'ddos-secure-test', 'diamond-support@radware.com', 'dineshg@radware.com', 'djayanthi', 'dkumari', 'donald', 'draco-sw', 'drorp@radware.com', 'elevy@websense.com', 'evgeny.vovk@kaspersky.com', 'gdmurali', 'ghuberty', 'gmontanez', 'grane', 'gtempel@trivenidigital.com', 'hschang', 'igor.gusarov@kaspersky.com', 'israels@radware.com', 'jerryzhao', 'jgaudutis', 'jhammond', 'jkotham', 'jojyv', 'jonathanj@radware.com', 'kprema', 'kraju@trivenidigital.com', 'ksarguna', 'ksuresh', 'kumarav', 'lchovan', 'letendre@avaya.com', 'lewang', 'liorr@radware.com', 'lmrichardson@avaya.com', 'marcelod@radware.com', 'mchakradeo@websense.com', 'mcorl@trivenidigital.com', 'mktiwari', 'mmadziva@avaya.com', 'mpantelimon', 'mtippett', 'mzubair', 'nshimuk', 'oleg.mikhalsky@kaspersky.com', 'otamoshevsky', 'oyarom@websense.com', 'pandya@avaya.com', 'philchen', 'pjhaveri', 'pkatti', 'pscanlon', 'ptkumar', 'rahulc', 'rajveers@radware.com', 'ranga@trivenidigital.com', 'rozenthal@avaya.com', 'sbennur', 'shunt@trivenidigital.com', 'sju', 'skpatel', 'slt-builder', 'sparva', 'support@trivenidigital.com', 'syhong@avaya.com', 'tavorb@radware.com', 'test-esbu', 'test-ft-platform', 'test-hss', 'test-jrs', 'test-junoscore', 'tkashyap', 'tsuryap', 'vbaddour@websense.com', 'vidyadharj', 'vijayk-managers', 'vkisara', 'wlan-build-eng', 'yuvcohen@avaya.com', 'zchang'], key=str.lower):           
    print 'test for unmanaged() passed'
else:
    print 'test for unmanaged() failed'
    
# Test 7: checks a list of all managers who are unmanaged
if H.unmanaged_managers() == sorted(['pmorgan', 'rvenket', 'araldo', 'dhuggins', 'lmoss', 'slyons', 'Mahipal', 'cbardenheuer', 'gerri', 'mbusselen', 'qzhang', 'tmorita', 'gcafaro', 'gdasmalchi', 'agrant', 'hbedekar', 'martyg', 'larrytam', 'jnbrown', 'mopificius', 'tsauter', 'nik', 'ceciloh', 'cdebrito', 'sdales', 'michel', 'isara', 'gloriac', 'jpflaum', 'regonini', 'jstaley', 'asingla', 'vmakeev', 'abrahami', 'rgilmartin', 'pmossman', 'abhushan', 'wearley', 'apickering', 'jorbe', 'rogrady', 'briccitelli', 'aminer', 'ravic', 'dkamensky', 'rchauhan', 'aleconte', 'kevin', 'wilsont', 'ujwal', 'perdikou', 'cwymes', 'tdesrues', 'bbeaudet', 'dmurray', 'scottn', 'mcallahan', 'makotoaoki', 'fwaldsch', 'sarahsmith', 'asotillo', 'abaziz', 'kctan', 'steier', 'broach', 'jstauffer', 'webel', 'mquartermaine', 'rauslander', 'skraman', 'acajano', 'rskinner', 'bsia', 'jflowers', 'rgopal', 'raghu', 'mablett', 'ktank', 'agriffin', 'bnrosenberg', 'mikemarcellin', 'seandolan', 'cmanca', 'wkamal', 'eyu', 'rproulx', 'prajidi', 'czhou', 'kbchai', 'ghvandewouw', 'jbristow', 'EKim', 'nathanm', 'jbelcher', 'mhurley', 'danielw', 'jkeeler', 'gholland', 'bdurand', 'neely', 'shaun', 'Fsilva', 'nvitro', 'rdenholm', 'kevina'], key=str.lower):   
    print 'test for unmanaged_managers() passed'
else:
    print 'test for unmanaged_managers() failed'
    
    