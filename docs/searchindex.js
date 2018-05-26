Search.setIndex({docnames:["index","modules","pcari","pcari.admin","pcari.apps","pcari.management","pcari.management.commands","pcari.management.commands.cleantext","pcari.management.commands.makedbtrans","pcari.management.commands.makemessages","pcari.models","pcari.signals","pcari.templatetags","pcari.templatetags.localize_url","pcari.views"],envversion:52,filenames:["index.rst","modules.rst","pcari.rst","pcari.admin.rst","pcari.apps.rst","pcari.management.rst","pcari.management.commands.rst","pcari.management.commands.cleantext.rst","pcari.management.commands.makedbtrans.rst","pcari.management.commands.makemessages.rst","pcari.models.rst","pcari.signals.rst","pcari.templatetags.rst","pcari.templatetags.localize_url.rst","pcari.views.rst"],objects:{"":{pcari:[2,0,0,"-"]},"pcari.admin":{CommentAdmin:[3,1,1,""],CommentRatingAdmin:[3,1,1,""],LocationAdmin:[3,1,1,""],MalasakitAdminSite:[3,1,1,""],OptionQuestionAdmin:[3,1,1,""],OptionQuestionChoiceAdmin:[3,1,1,""],QualitativeQuestionAdmin:[3,1,1,""],QuantitativeQuestionAdmin:[3,1,1,""],QuantitativeQuestionRatingAdmin:[3,1,1,""],RespondentAdmin:[3,1,1,""]},"pcari.admin.CommentAdmin":{actions:[3,2,1,""],display_mean_score:[3,3,1,""],display_message:[3,3,1,""],display_wilson_score:[3,3,1,""],flag_comments:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],num_ratings:[3,3,1,""],search_fields:[3,2,1,""],unflag_comments:[3,3,1,""]},"pcari.admin.CommentRatingAdmin":{get_comment_message:[3,3,1,""],get_score:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],readonly_fields:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.LocationAdmin":{actions:[3,2,1,""],disable_as_input_options:[3,3,1,""],display_country:[3,3,1,""],display_division:[3,3,1,""],display_municipality:[3,3,1,""],display_province:[3,3,1,""],empty_value_display:[3,2,1,""],enable_as_input_options:[3,3,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.MalasakitAdminSite":{change_bloom_icon:[3,3,1,""],change_landing_image:[3,3,1,""],configuration:[3,3,1,""],filter_actions:[3,3,1,""],get_urls:[3,3,1,""],site_header:[3,2,1,""],site_title:[3,2,1,""],statistics:[3,3,1,""]},"pcari.admin.OptionQuestionAdmin":{empty_value_display:[3,2,1,""],get_prompt:[3,3,1,""],get_tag:[3,3,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],options:[3,3,1,""],search_fields:[3,2,1,""]},"pcari.admin.OptionQuestionChoiceAdmin":{list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],option_display:[3,3,1,""],question_prompt:[3,3,1,""],search_fields:[3,2,1,""]},"pcari.admin.QualitativeQuestionAdmin":{actions:[3,2,1,""],display_question_num_comments:[3,3,1,""],empty_value_display:[3,2,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.QuantitativeQuestionAdmin":{actions:[3,2,1,""],empty_value_display:[3,2,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],num_ratings:[3,3,1,""],search_fields:[3,2,1,""]},"pcari.admin.QuantitativeQuestionRatingAdmin":{get_score:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],question_prompt:[3,3,1,""],readonly_fields:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.RespondentAdmin":{comments:[3,3,1,""],display_location:[3,3,1,""],empty_value_display:[3,2,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.apps":{PCARIConfig:[4,1,1,""]},"pcari.apps.PCARIConfig":{name:[4,2,1,""],ready:[4,3,1,""],verbose_name:[4,2,1,""]},"pcari.management":{commands:[6,0,0,"-"]},"pcari.management.commands":{BatchProcessingCommand:[6,1,1,""],cleantext:[7,0,0,"-"],makedbtrans:[8,0,0,"-"],makemessages:[9,0,0,"-"]},"pcari.management.commands.BatchProcessingCommand":{add_arguments:[6,3,1,""],handle:[6,3,1,""],postprocess:[6,3,1,""],precondition_check:[6,3,1,""],preprocess:[6,3,1,""],process:[6,3,1,""]},"pcari.management.commands.cleantext":{Command:[7,1,1,""]},"pcari.management.commands.cleantext.Command":{help:[7,2,1,""],precondition_check:[7,3,1,""],process:[7,3,1,""]},"pcari.management.commands.makedbtrans":{Command:[8,1,1,""]},"pcari.management.commands.makedbtrans.Command":{OUTPUT_FILE_KEY:[8,2,1,""],add_arguments:[8,3,1,""],help:[8,2,1,""],postprocess:[8,3,1,""],precondition_check:[8,3,1,""],preprocess:[8,3,1,""],process:[8,3,1,""]},"pcari.management.commands.makemessages":{Command:[9,1,1,""]},"pcari.management.commands.makemessages.Command":{write_po_file:[9,3,1,""]},"pcari.models":{Comment:[10,1,1,""],CommentRating:[10,1,1,""],LANGUAGE_VALIDATOR:[10,2,1,""],Location:[10,1,1,""],OptionQuestion:[10,1,1,""],OptionQuestionChoice:[10,1,1,""],QualitativeQuestion:[10,1,1,""],QuantitativeQuestion:[10,1,1,""],QuantitativeQuestionRating:[10,1,1,""],Respondent:[10,1,1,""],get_concrete_fields:[10,5,1,""],get_direct_fields:[10,5,1,""]},"pcari.models.Comment":{DoesNotExist:[10,4,1,""],MAX_MESSAGE_DISPLAY_LENGTH:[10,2,1,""],MultipleObjectsReturned:[10,4,1,""],flagged:[10,2,1,""],language:[10,2,1,""],message:[10,2,1,""],objects:[10,2,1,""],original:[10,2,1,""],question:[10,2,1,""],tag:[10,2,1,""],word_count:[10,2,1,""]},"pcari.models.CommentRating":{DoesNotExist:[10,4,1,""],MultipleObjectsReturned:[10,4,1,""],comment:[10,2,1,""],objects:[10,2,1,""]},"pcari.models.Location":{DoesNotExist:[10,4,1,""],MultipleObjectsReturned:[10,4,1,""],country:[10,2,1,""],division:[10,2,1,""],enabled:[10,2,1,""],municipality:[10,2,1,""],objects:[10,2,1,""],province:[10,2,1,""]},"pcari.models.OptionQuestion":{DoesNotExist:[10,4,1,""],INPUT_TYPE_CHOICES:[10,2,1,""],MultipleObjectsReturned:[10,4,1,""],_options_text:[10,2,1,""],clean_fields:[10,3,1,""],input_type:[10,2,1,""],objects:[10,2,1,""],options:[10,2,1,""]},"pcari.models.OptionQuestionChoice":{DoesNotExist:[10,4,1,""],MultipleObjectsReturned:[10,4,1,""],clean:[10,3,1,""],objects:[10,2,1,""],option:[10,2,1,""],question:[10,2,1,""]},"pcari.models.QualitativeQuestion":{DoesNotExist:[10,4,1,""],MultipleObjectsReturned:[10,4,1,""],input_type:[10,2,1,""],objects:[10,2,1,""]},"pcari.models.QuantitativeQuestion":{DoesNotExist:[10,4,1,""],INPUT_TYPE_CHOICES:[10,2,1,""],MultipleObjectsReturned:[10,4,1,""],input_type:[10,2,1,""],left_anchor:[10,2,1,""],max_score:[10,2,1,""],min_score:[10,2,1,""],objects:[10,2,1,""],right_anchor:[10,2,1,""]},"pcari.models.QuantitativeQuestionRating":{DoesNotExist:[10,4,1,""],MultipleObjectsReturned:[10,4,1,""],clean:[10,3,1,""],objects:[10,2,1,""],question:[10,2,1,""]},"pcari.models.Respondent":{DoesNotExist:[10,4,1,""],GENDERS:[10,2,1,""],MultipleObjectsReturned:[10,4,1,""],age:[10,2,1,""],comments:[10,2,1,""],gender:[10,2,1,""],language:[10,2,1,""],location:[10,2,1,""],num_comments_rated:[10,2,1,""],num_questions_rated:[10,2,1,""],objects:[10,2,1,""],related_object:[10,2,1,""]},"pcari.signals":{extend_sqlite:[11,5,1,""],make_stddev_aggregate:[11,5,1,""]},"pcari.templatetags":{localize_url:[13,0,0,"-"]},"pcari.templatetags.localize_url":{localize_url:[13,5,1,""]},"pcari.views":{calculate_principal_components:[14,5,1,""],export_data:[14,5,1,""],fetch_comments:[14,5,1,""],fetch_option_questions:[14,5,1,""],fetch_qualitative_questions:[14,5,1,""],fetch_quantitative_questions:[14,5,1,""],fetch_question_ratings:[14,5,1,""],generate_ratings_matrix:[14,5,1,""],handle_internal_server_error:[14,5,1,""],handle_page_not_found:[14,5,1,""],landing:[14,5,1,""],normalize_ratings_matrix:[14,5,1,""],peer_responses:[14,5,1,""],qualitative_questions:[14,5,1,""],save_response:[14,5,1,""]},pcari:{admin:[3,0,0,"-"],apps:[4,0,0,"-"],management:[5,0,0,"-"],models:[10,0,0,"-"],signals:[11,0,0,"-"],templatetags:[12,0,0,"-"],views:[14,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","exception","Python exception"],"5":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:exception","5":"py:function"},terms:{"abstract":10,"case":14,"class":[3,4,6,7,8,9,10,11],"default":[9,14],"export":[6,8,14],"function":[3,11],"int":[10,14],"new":14,"return":[11,13,14],"short":10,"static":14,"switch":13,For:10,That:14,The:[0,3,6,8,10,13,14],These:14,With:13,_options_text:10,abbrevi:10,accessor:10,accomplish:3,action:[3,6,11],action_nam:3,activ:14,add_argu:[6,8],admin:[1,2],admin_sit:3,administr:10,adminsit:3,adminviewmixin:3,age:[3,10,14],aggreg:11,all:[6,8,10],allow:3,also:10,analog:10,analysi:14,anchor:14,ani:13,anoth:14,answer:10,api:[10,14],app:[1,2],app_modul:4,app_nam:4,appconfig:4,applic:[0,3,4,14],area:10,arg:[6,10,14],argument:[6,8],around:10,arrai:14,ask:[10,14],assess:0,associ:[3,10],asynchron:14,attach:[10,14],attribut:10,augment:3,author:14,automat:10,backend:11,bad:14,barangai:10,base:[3,4,6,7,8,9,10],basecommand:6,basic:7,batch:[6,7,8],batchprocessingcommand:[6,7,8],becom:0,been:3,befor:[9,14],behavior:[3,4],better:0,between:10,blank:10,bloom:3,bodi:14,bool:[10,14],bound:10,broadli:14,bulk:3,button:10,cach:14,calcul:[11,14],calculate_principal_compon:14,can:[0,8,10,14],categor:14,center:14,change_bloom_icon:3,change_landing_imag:3,charact:[7,10],choic:[3,10,14],chosen:11,citi:10,clean:[6,7,10],clean_field:10,cleantext:[5,6],client:14,close:[6,8],code:[0,10,13,14],collabor:0,collect:[0,10],column:14,command:5,commanderror:[6,8],comment:[3,10,14],comment__messag:3,commentadmin:3,commentr:[3,10],commentratingadmin:3,common:6,commun:0,compat:7,compil:10,complet:14,completed_survei:3,compon:14,concret:10,config:4,configur:[3,4],conjunct:9,connect:11,consist:10,contain:[7,10,14],content:[0,1,10],contenttyp:10,context:10,contigu:10,contrib:3,contribut:0,core:[6,9,10],correspond:10,counti:10,countri:[3,10],creat:[11,14],critic:11,csv:14,current:[10,14],custom:[3,4,6,11,13],customiz:0,data:[6,14],data_format:14,databas:[8,10,14],dataset:14,decor:14,decreas:14,defin:[3,4,6,10,11,13,14],definit:10,delimit:10,deriv:10,describ:10,design:10,deviat:11,dict:[6,8,14],did:10,disabl:3,disable_as_input_opt:3,displai:10,display_countri:3,display_divis:3,display_loc:3,display_mean_scor:3,display_messag:3,display_municip:3,display_provinc:3,display_question_num_com:3,display_wilson_scor:3,divis:[3,10],django:[0,3,4,6,8,9,10,11,14],doesnotexist:10,download:14,dropdown:10,dure:14,dynam:14,each:[10,14],element:10,ellipsoid:14,empti:[3,7,10],empty_value_displai:3,enabl:[3,4,10],enable_as_input_opt:3,end:10,endpoint:14,entri:10,error:14,etc:10,event:11,exampl:10,except:[6,8,10],exclud:10,exist:9,export_data:14,export_to_feature_phon:3,express:10,extend:9,extend_sqlit:11,fall:10,fals:[6,7,8,9,11],feedback:0,femal:10,fetch:14,fetch_com:14,fetch_option_quest:14,fetch_qualitative_quest:14,fetch_quantitative_quest:14,fetch_question_r:14,field:[6,7,8,10],field_nam:[6,7,8],file:[3,6,8,9,14],filter:0,filter_act:3,first:[10,14],flag:[3,10],flag_com:3,flood:0,follow:14,form:14,format:14,found:14,framework:10,from:[6,7,8,10,14],full:10,full_clean:14,further:10,gender:[3,10,14],gener:[10,13,14],generate_ratings_matrix:14,get:[0,14],get_act:3,get_comment_messag:3,get_concrete_field:10,get_direct_field:10,get_prompt:3,get_scor:3,get_tag:3,get_url:3,github:0,given:[3,6,13],gnu:8,govern:10,group:14,guidelin:0,handl:[4,6],handle_internal_server_error:14,handle_page_not_found:14,has:3,have:3,help:[7,8],high:14,histori:14,how:[3,10,14],html:14,http:14,httprespons:14,httpresponsebadrequest:14,icon:3,identifi:14,ignor:14,imag:3,implement:11,imput:14,index:0,indic:10,indici:14,infer:10,infin:10,inform:[3,10],input:[3,10,14],input_typ:[10,14],input_type_choic:10,inspect:[6,8,10],instanc:[6,7,8,10,14],instruct:0,integr:0,interfac:10,intern:[10,14],introduct:14,invalid:14,item:14,its:10,itself:10,job:[6,8],json:[10,14],jsonrespons:14,keyword:[6,8],known:3,kwarg:[10,14],land:[3,13,14],languag:[3,10,13,14],language_valid:10,larg:14,largest:10,layer:10,lead:7,left:[10,14],left_anchor:[10,14],legal:10,lend:14,length:14,letter:10,limit:14,line:[6,7,8],list:[3,10,14],list_displai:3,list_display_link:3,list_filt:3,live:0,local:[0,9,13],localize_url:12,locat:[3,10,14],locationadmin:3,logic:14,lower:10,mai:[3,14],make_stddev_aggreg:11,makedbtran:[5,6,9],makemessag:[5,6],malasakit:[3,10],malasakitadminsit:3,male:10,malform:14,manag:10,mani:[3,14],manipul:[6,10],map:14,match:10,matrix:14,max:14,max_message_display_length:10,max_scor:[10,14],maximum:10,mean:14,member:14,menu:10,merg:[8,9],messag:[3,9,10,14],met:[6,8],method:3,min:14,min_scor:[10,14],minimum:10,miss:14,model:[1,2,3,6,7,8,14],model_nam:[6,7,8],modif:14,modul:[0,1],monkei:11,msg:14,msgcat:8,multipl:10,multipleobjectsreturn:10,municip:[3,10],must:[3,10],name:[3,4,6,10],nan:14,nativ:11,ndarrai:14,necessari:[6,8],need:14,neg:10,no_color:[6,7,8,9],none:[3,6,7,8,9,10,11],nonexist:14,normal:14,normalize_ratings_matrix:14,normalized_r:14,notic:14,num_comments_r:[3,10],num_compon:14,num_questions_r:[3,10],num_rat:3,number:[10,14],numer:10,numpi:14,object:[10,14],objectdoesnotexist:10,obtain:14,onc:10,one:[10,14],onetoonefield:10,onli:[10,14],onto:14,open:[6,8,10],oper:[6,14],option:[3,6,7,8,10,14],option_displai:3,option_quest:3,optionquest:[3,10],optionquestionadmin:3,optionquestionchoic:[3,10],optionquestionchoiceadmin:3,order:14,origin:[10,14],other:[9,10,14],otherwis:[10,14],output:8,output_file_kei:8,own:8,packag:1,page:[0,3,14],pair:10,panel:3,paramet:[3,6,8,11,13,14],parser:[6,8],particip:10,participatori:0,particular:10,pass:11,patch:11,payload:14,pcari:0,pcariconfig:4,peer:0,peer_respons:14,perform:[6,7,11,14],person:14,philippin:10,place:10,placehold:3,platform:0,pos:14,posit:10,possibl:10,postprocess:[6,8],pot:[8,9],potfil:9,precinct:10,precondit:[6,8],precondition_check:[6,7,8],prefer:10,prepar:[0,6,8,9],preprocess:[6,8],present:10,princip:14,prior:[6,8],process:[6,7,8],product:11,progress:10,project:[0,14],prompt:[3,14],properti:14,provid:[6,14],provinc:[3,10],pull:8,purpos:14,pysqlit:11,python:[6,10,14],qid:14,qualit:[0,10,14],qualitative_quest:14,qualitativequest:[3,10],qualitativequestionadmin:3,quantit:[0,10,14],quantitativequest:[3,10],quantitativequestionadmin:3,quantitativequestionr:[3,10],quantitativequestionratingadmin:3,queryset:[3,10,14],question:[3,10,14],question_id:14,question_id_map:14,question_prompt:3,radio:10,rais:[6,8,10],rang:10,rate:[3,10,14],ratings_matrix:14,ratingstatisticsmanag:10,reach:10,readi:4,readonly_field:3,receiv:14,refer:[3,4,6,10,11,14],regist:3,regular:10,relat:10,related_nam:10,related_object:10,render:[3,10,14],replac:7,repositori:0,repres:[10,14],represent:[10,14],request:[3,14],resid:10,respect:14,respond:[3,10,14],respondent_id_map:14,respondentadmin:3,respons:[10,14],responseadmin:3,restaur:10,restrict:3,revers:10,reverseonetoonedescriptor:10,review:10,right:[10,14],right_anchor:[10,14],roughli:10,row:14,sampl:[11,13],save:[3,14],save_respons:14,score:[3,10,14],score_sem:14,search:0,search_field:3,second:[10,14],see:[0,14],select:[3,10,14],sem:14,send:14,sequenc:6,serial:10,server:14,servic:14,set:[10,13,14],setup:0,shorthand:10,should:[3,10,11,14],show:[10,14],side:10,signal:[1,2,4],similarli:10,singl:[10,14],site:3,site_head:3,site_titl:3,skip:10,slider:10,smallest:10,some:[6,8],speak:10,special:11,specifi:[7,10,14],sqlite:11,staff:3,stage:10,standard:11,start:[0,4,13],state:10,statist:[3,14],statu:14,stderr:[6,7,8,9],stdout:[6,7,8,9],store:8,str:[6,10,14],string:[3,7,8,10,13,14],structur:[10,14],submit:14,submitted_personal_data:3,submodul:[0,1,5],successfulli:14,suggest:14,summari:10,supplementari:0,survei:[10,14],syntact:14,tag:[3,10,13,14],take:3,taken:11,templat:6,termin:[6,8],text:[7,8,10],textarea:10,them:8,themselv:14,thi:[3,4,6,7,8,10,11,13,14],three:14,through:14,time:10,timestamp:3,togeth:9,town:10,trail:7,translat:[8,9,10,14],treat:10,tupl:[10,14],two:[10,14],type:[10,14],typhoon:0,typic:14,unflag:3,unflag_com:3,unit:10,unord:10,unseri:10,upper:10,url:13,url_exampl:13,url_root:13,use:[9,10,14],used:[10,14],useful:6,user:[3,7,10,14],uses:11,using:8,util:[6,7],uuid:14,valid:[3,10,14],validationerror:10,valu:[7,10,14],vari:10,vector:14,verbose_nam:4,veri:14,verifi:7,view:[1,2],wai:[0,10],ward:10,were:[3,14],what:10,when:[4,14],where:11,whether:[10,11],which:[6,10,14],whitespac:[7,10],whose:[3,14],wide:4,wiki:0,without:14,word:10,word_count:10,worker:14,world:10,would:[6,10],wrap:3,wrapper:10,write:[6,8,14],write_po_fil:9,written:[0,10,14],xlsx:14,year:10,yield:3,zero:14},titles:["Welcome to Malasakit\u2019s documentation!","pcari","pcari package","pcari.admin module","pcari.apps module","pcari.management package","pcari.management.commands package","pcari.management.commands.cleantext module","pcari.management.commands.makedbtrans module","pcari.management.commands.makemessages module","pcari.models module","pcari.signals module","pcari.templatetags package","pcari.templatetags.localize_url module","pcari.views module"],titleterms:{admin:3,app:4,cleantext:7,command:[6,7,8,9],content:[2,5,6,12],document:0,indic:0,localize_url:13,makedbtran:8,makemessag:9,malasakit:0,manag:[5,6,7,8,9],model:10,modul:[2,3,4,5,6,7,8,9,10,11,12,13,14],packag:[2,5,6,12],pcari:[1,2,3,4,5,6,7,8,9,10,11,12,13,14],signal:11,submodul:[2,6,12],subpackag:5,tabl:0,templatetag:[12,13],view:14,welcom:0}})