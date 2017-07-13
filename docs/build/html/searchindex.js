Search.setIndex({docnames:["index","modules","pcari","pcari.admin","pcari.apps","pcari.management","pcari.management.commands","pcari.management.commands.cleantext","pcari.management.commands.makedbtrans","pcari.management.commands.makemessages","pcari.models","pcari.signals","pcari.templatetags","pcari.templatetags.localize_url","pcari.views"],envversion:52,filenames:["index.rst","modules.rst","pcari.rst","pcari.admin.rst","pcari.apps.rst","pcari.management.rst","pcari.management.commands.rst","pcari.management.commands.cleantext.rst","pcari.management.commands.makedbtrans.rst","pcari.management.commands.makemessages.rst","pcari.models.rst","pcari.signals.rst","pcari.templatetags.rst","pcari.templatetags.localize_url.rst","pcari.views.rst"],objects:{"":{pcari:[2,0,0,"-"]},"pcari.admin":{CommentAdmin:[3,1,1,""],CommentRatingAdmin:[3,1,1,""],HistoryAdmin:[3,1,1,""],MalasakitAdminSite:[3,1,1,""],QualitativeQuestionAdmin:[3,1,1,""],QuantitativeQuestionAdmin:[3,1,1,""],QuantitativeQuestionRatingAdmin:[3,1,1,""],QuestionAdmin:[3,1,1,""],RespondentAdmin:[3,1,1,""],ResponseAdmin:[3,1,1,""],export_selected_as_csv:[3,4,1,""],export_selected_as_xlsx:[3,4,1,""]},"pcari.admin.CommentAdmin":{actions:[3,2,1,""],display_mean_score:[3,3,1,""],display_message:[3,3,1,""],flag_comments:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""],unflag_comments:[3,3,1,""]},"pcari.admin.CommentRatingAdmin":{get_comment_message:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],readonly_fields:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.HistoryAdmin":{actions:[3,2,1,""],get_readonly_fields:[3,3,1,""],mark_active:[3,3,1,""],mark_inactive:[3,3,1,""],save_as_continue:[3,2,1,""],save_model:[3,3,1,""]},"pcari.admin.MalasakitAdminSite":{change_bloom_icon:[3,3,1,""],configuration:[3,3,1,""],get_urls:[3,3,1,""],site_header:[3,2,1,""],site_title:[3,2,1,""],statistics:[3,3,1,""]},"pcari.admin.QualitativeQuestionAdmin":{list_display:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.QuantitativeQuestionAdmin":{list_display:[3,2,1,""],list_filter:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.QuantitativeQuestionRatingAdmin":{get_question_prompt:[3,3,1,""],list_display:[3,2,1,""],list_display_links:[3,2,1,""],list_filter:[3,2,1,""],readonly_fields:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.QuestionAdmin":{list_select_related:[3,2,1,""]},"pcari.admin.RespondentAdmin":{comments_made:[3,3,1,""],display_location:[3,3,1,""],empty_value_display:[3,2,1,""],list_display:[3,2,1,""],list_filter:[3,2,1,""],list_select_related:[3,2,1,""],search_fields:[3,2,1,""]},"pcari.admin.ResponseAdmin":{empty_value_display:[3,2,1,""],list_select_related:[3,2,1,""],ordering:[3,2,1,""]},"pcari.apps":{PCARIConfig:[4,1,1,""]},"pcari.apps.PCARIConfig":{name:[4,2,1,""],ready:[4,3,1,""],verbose_name:[4,2,1,""]},"pcari.management":{commands:[6,0,0,"-"]},"pcari.management.commands":{BatchProcessingCommand:[6,1,1,""],cleantext:[7,0,0,"-"],makedbtrans:[8,0,0,"-"],makemessages:[9,0,0,"-"]},"pcari.management.commands.BatchProcessingCommand":{add_arguments:[6,3,1,""],handle:[6,3,1,""],postprocess:[6,3,1,""],precondition_check:[6,3,1,""],preprocess:[6,3,1,""],process:[6,3,1,""]},"pcari.management.commands.cleantext":{Command:[7,1,1,""]},"pcari.management.commands.cleantext.Command":{help:[7,2,1,""],precondition_check:[7,3,1,""],process:[7,3,1,""]},"pcari.management.commands.makedbtrans":{Command:[8,1,1,""]},"pcari.management.commands.makedbtrans.Command":{OUTPUT_FILE_KEY:[8,2,1,""],add_arguments:[8,3,1,""],help:[8,2,1,""],postprocess:[8,3,1,""],precondition_check:[8,3,1,""],preprocess:[8,3,1,""],process:[8,3,1,""]},"pcari.management.commands.makemessages":{Command:[9,1,1,""]},"pcari.management.commands.makemessages.Command":{write_po_file:[9,3,1,""]},"pcari.models":{Comment:[10,1,1,""],CommentRating:[10,1,1,""],History:[10,1,1,""],LANGUAGES:[10,2,1,""],MODELS:[10,2,1,""],OptionQuestion:[10,1,1,""],OptionQuestionChoice:[10,1,1,""],QualitativeQuestion:[10,1,1,""],QuantitativeQuestion:[10,1,1,""],QuantitativeQuestionRating:[10,1,1,""],Question:[10,1,1,""],Respondent:[10,1,1,""],Response:[10,1,1,""],StatisticsMixin:[10,1,1,""]},"pcari.models.Comment":{DoesNotExist:[10,5,1,""],MAX_COMMENT_DISPLAY_LEN:[10,2,1,""],MultipleObjectsReturned:[10,5,1,""],flagged:[10,2,1,""],language:[10,2,1,""],message:[10,2,1,""],objects:[10,2,1,""],question:[10,2,1,""],tag:[10,2,1,""],word_count:[10,2,1,""]},"pcari.models.CommentRating":{DoesNotExist:[10,5,1,""],MultipleObjectsReturned:[10,5,1,""],comment:[10,2,1,""],objects:[10,2,1,""]},"pcari.models.History":{Meta:[10,1,1,""],active:[10,2,1,""],diff:[10,3,1,""],make_copy:[10,3,1,""],predecessor:[10,2,1,""]},"pcari.models.History.Meta":{"abstract":[10,2,1,""]},"pcari.models.OptionQuestion":{DoesNotExist:[10,5,1,""],INPUT_TYPE_CHOICES:[10,2,1,""],MultipleObjectsReturned:[10,5,1,""],_options_text:[10,2,1,""],input_type:[10,2,1,""],objects:[10,2,1,""],options:[10,2,1,""]},"pcari.models.OptionQuestionChoice":{DoesNotExist:[10,5,1,""],MultipleObjectsReturned:[10,5,1,""],clean:[10,3,1,""],objects:[10,2,1,""],option:[10,2,1,""],question:[10,2,1,""]},"pcari.models.QualitativeQuestion":{DoesNotExist:[10,5,1,""],MultipleObjectsReturned:[10,5,1,""],input_type:[10,2,1,""],objects:[10,2,1,""]},"pcari.models.QuantitativeQuestion":{DoesNotExist:[10,5,1,""],INPUT_TYPE_CHOICES:[10,2,1,""],MultipleObjectsReturned:[10,5,1,""],input_type:[10,2,1,""],left_anchor:[10,2,1,""],max_score:[10,2,1,""],min_score:[10,2,1,""],objects:[10,2,1,""],right_anchor:[10,2,1,""]},"pcari.models.QuantitativeQuestionRating":{DoesNotExist:[10,5,1,""],MultipleObjectsReturned:[10,5,1,""],clean:[10,3,1,""],objects:[10,2,1,""],question:[10,2,1,""]},"pcari.models.Question":{Meta:[10,1,1,""],prompt:[10,2,1,""],tag:[10,2,1,""]},"pcari.models.Question.Meta":{"abstract":[10,2,1,""]},"pcari.models.Respondent":{DoesNotExist:[10,5,1,""],GENDERS:[10,2,1,""],MultipleObjectsReturned:[10,5,1,""],age:[10,2,1,""],comments:[10,2,1,""],completed_survey:[10,2,1,""],gender:[10,2,1,""],language:[10,2,1,""],location:[10,2,1,""],num_comments_rated:[10,2,1,""],num_questions_rated:[10,2,1,""],objects:[10,2,1,""],submitted_personal_data:[10,2,1,""]},"pcari.models.Response":{Meta:[10,1,1,""],respondent:[10,2,1,""],timestamp:[10,2,1,""]},"pcari.models.Response.Meta":{"abstract":[10,2,1,""]},"pcari.signals":{resolve_history_on_deletion:[11,4,1,""],store_successors:[11,4,1,""]},"pcari.templatetags":{localize_url:[13,0,0,"-"]},"pcari.templatetags.localize_url":{localize_url:[13,4,1,""]},"pcari.views":{calculate_principal_components:[14,4,1,""],end:[14,4,1,""],export_data:[14,4,1,""],fetch_comments:[14,4,1,""],fetch_qualitative_questions:[14,4,1,""],fetch_quantitative_questions:[14,4,1,""],fetch_question_ratings:[14,4,1,""],generate_ratings_matrix:[14,4,1,""],handle_internal_server_error:[14,4,1,""],handle_page_not_found:[14,4,1,""],index:[14,4,1,""],landing:[14,4,1,""],normalize_ratings_matrix:[14,4,1,""],peer_responses:[14,4,1,""],personal_information:[14,4,1,""],qualitative_questions:[14,4,1,""],rate_comments:[14,4,1,""],save_response:[14,4,1,""]},pcari:{admin:[3,0,0,"-"],apps:[4,0,0,"-"],management:[5,0,0,"-"],models:[10,0,0,"-"],signals:[11,0,0,"-"],templatetags:[12,0,0,"-"],views:[14,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","function","Python function"],"5":["py","exception","Python exception"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:function","5":"py:exception"},terms:{"abstract":[3,10],"boolean":10,"case":14,"class":[3,4,6,7,8,9,10],"default":[9,10,14],"export":[3,6,8,14],"function":3,"new":10,"return":[10,13,14],"short":[10,14],"switch":13,"true":3,For:10,That:14,The:[10,13,14],With:13,_options_text:10,abbrevi:10,accept:10,access:10,act:10,action:[3,6,11],activ:[3,10,14],add:10,add_argu:[6,8],admin:[1,2],admin_sit:3,adminsit:3,after:10,age:[3,10,14],all:[6,10,14],ani:13,anoth:[10,14],answer:10,app:[1,2],app_modul:4,app_nam:4,appconfig:4,applic:[3,4,14],arg:[6,10,14],around:10,arrai:14,ask:[10,14],attach:10,attribut:[10,14],augment:3,author:[10,14],automat:10,barangai:10,base:[3,4,6,7,8,9,10],basecommand:6,basic:7,batch:[6,7],batchprocessingcommand:[6,7,8],becaus:10,befor:[9,14],behavior:3,bloom:[3,14],bodi:14,bookkeep:10,bound:10,bulk:3,button:10,calcul:14,calculate_principal_compon:14,can:[8,10,14],capabl:10,center:14,chang:[3,10],change_bloom_icon:3,charact:7,choic:10,cid:14,citi:10,clean:[6,7,10],cleantext:[2,5,6],client:14,close:6,code:[10,13,14],collect:10,column:14,comma:[3,14],command:[2,5],comment:[3,10,14],comment__messag:3,comment_r:3,commentadmin:3,commentr:[3,10],commentratingadmin:3,comments_mad:3,common:6,compat:7,complet:[10,14],completed_survei:[3,10],compon:14,config:4,configur:[3,4],conjunct:9,consid:10,consist:10,contain:[7,10,14],content:[1,10,14],context:10,contigu:10,contrib:3,copi:10,core:[6,9,10],creat:10,csv:[3,14],current:10,custom:[3,13],cyclic:10,dangl:11,data:[6,10,14],data_format:14,databas:[8,10,14],dataset:14,date:10,defin:[3,4,6,10,11,13,14],definit:10,delimit:10,deriv:[10,11],describ:10,descript:[10,14],determin:10,dictionari:[10,14],did:10,diff:10,differ:10,display_loc:3,display_mean_scor:3,display_messag:3,django:[3,4,6,8,9,10],doe:[10,14],doesnotexist:10,dropdown:10,each:[10,14],edit:10,effect:10,element:10,ellipsoid:14,empti:[3,7],empty_value_displai:3,end:[10,14],english:10,ensur:11,entir:10,entri:10,error:14,essenti:10,event:11,excel:3,except:[6,10],exclud:10,exist:[9,10,14],export_data:14,export_selected_as_csv:3,export_selected_as_xlsx:3,extend:9,fals:[3,6,7,8,9,10],featur:14,femal:10,fetch:14,fetch_com:14,fetch_qualitative_quest:14,fetch_quantitative_quest:14,fetch_question_r:14,field:[6,7,8,10,14],field_nam:[6,7,8],file:[3,6,8,9,14],find:10,first:[10,14],flag:[3,10],flag_com:3,follow:14,form:[3,10,14],format:14,found:14,from:[7,8,10,11,14],full:10,further:10,gender:[3,10,14],gener:[10,13,14],generate_ratings_matrix:14,get:14,get_comment_messag:3,get_question_prompt:3,get_readonly_field:3,get_url:3,given:[6,10,13],gnu:8,handl:[4,6],handle_internal_server_error:14,handle_page_not_found:14,have:[10,11],help:[7,8],histori:[3,10,11],historyadmin:3,how:[3,10,14],http:14,httprespons:14,icon:3,identifi:14,ignor:14,imag:3,imput:14,inact:[3,10],incorrect:14,index:[0,14],indic:[10,14],indici:14,infer:10,infin:10,inform:[3,10,14],inherit:10,innput:10,input:10,input_typ:10,input_type_choic:10,insert:10,inspect:[6,10],instanc:[3,6,7,8,10,11,14],interfac:10,intern:14,its:10,itself:10,job:6,json:[10,14],jsonrespons:14,kei:14,kind:10,kwarg:[10,11,14],land:[13,14],languag:[3,10,13,14],largest:10,layer:10,lazili:10,lead:7,left:10,left_anchor:10,length:14,letter:10,limit:14,line:7,list:[10,14],list_displai:3,list_display_link:3,list_filt:3,list_select_rel:3,local:[9,10,13],localize_url:[2,12],locat:[3,10,14],logic:14,lookup:10,lower:10,made:10,mai:14,make:10,make_copi:10,makedbtran:[2,5,6,9],makemessag:[2,5,6],malasakit:[3,10],malasakitadminsit:3,male:10,malform:14,manag:[1,2,10],mani:[3,10,14],manipul:[6,10],map:[10,14],mark:[3,10],mark_act:3,mark_inact:3,matrix:14,max_comment_display_len:10,max_scor:10,maximum:10,mean:14,menu:10,merg:[8,9],messag:[3,9,10,14],meta:10,min_scor:10,minimum:10,miss:14,mixin:10,model:[1,2,3,6,7,8,11,14],model_nam:[6,7,8],modeladmin:3,modif:14,modul:[0,1],msg:14,msgcat:8,multipleobjectsreturn:10,municip:10,must:10,name:[3,4,10,14],nan:14,necessari:[6,10],need:14,neg:10,never:10,no_color:[6,7,8,9],none:[3,6,7,8,9,10],normal:14,normalize_ratings_matrix:14,normalized_r:14,num_comments_r:[3,10],num_compon:14,num_questions_r:[3,10],num_rat:3,number:[10,14],numer:[10,14],numpi:14,obj:3,object:[10,14],objectdoesnotexist:10,obtain:14,old:10,onc:10,one:[10,14],onli:[10,14],onto:14,open:[6,10],oper:6,option:[3,6,7,8,10,14],optionquest:10,optionquestionchoic:10,order:3,origin:14,other:[9,10,14],otherwis:10,output:8,output_file_kei:8,over:10,overwrit:10,own:8,packag:1,page:[0,3,14],pair:10,panel:3,paramet:[10,13,14],parser:[6,8],particip:10,particular:10,pcariconfig:4,peer_respons:14,perform:[6,7],person:14,personal_inform:14,philippin:10,pointer:11,pos:14,posit:[10,14],possibl:10,postprocess:[6,8],pot:[8,9],potfil:9,precondition_check:[6,7,8],predecessor:[10,11],prefer:10,prepar:[4,6,8,9],preprocess:[6,8],present:10,primari:14,princip:14,process:[6,7,8],progress:10,project:[10,14],prompt:[3,10],provid:[6,14],provinc:10,pull:[8,10],python:[10,14],qid:14,qualit:[10,14],qualitative_quest:14,qualitativequest:[10,14],qualitativequestionadmin:3,quantit:[10,14],quantitativequest:10,quantitativequestionadmin:3,quantitativequestionr:[3,10],quantitativequestionratingadmin:3,queryset:[3,10],question:[10,14],question__prompt:3,question_id_map:14,question_r:3,questionadmin:3,radio:10,rais:6,rang:10,rate:[10,14],rate_com:14,rather:10,ratings_matrix:14,reach:10,readi:4,readonly_field:3,receiv:14,record:10,redirect:14,refer:10,relat:10,relationship:10,render:[3,10,14],replac:7,repres:10,represent:14,request:[3,14],requr:14,resid:10,resolve_history_on_delet:11,resourc:4,respect:14,respond:[3,10,14],respondent_id_map:14,respondentadmin:3,respons:[3,10,14],responseadmin:3,revers:10,review:10,right:10,right_anchor:10,row:14,same:10,sampl:13,save:3,save_as_continu:3,save_model:3,save_respons:14,score:[3,10,14],search:0,search_field:3,second:[10,14],see:10,select:[3,10,14],self:10,sem:14,send:14,separ:[3,14],sequenc:6,serial:10,server:14,set:[10,13],shorthand:10,should:[3,10,11,14],show:[10,14],signal:[1,2],similarli:10,singl:[10,14],site:3,site_head:3,site_titl:3,skip:10,slider:10,smallest:10,some:10,special:[3,11],specifi:[7,10,14],spreadsheet:3,staff:3,stage:10,standard:14,start:13,statist:[3,10],statisticsmixin:10,stderr:[6,7,8,9],stdout:[6,7,8,9],store:8,store_successor:11,string:[7,8,10,13,14],structur:10,subclass:10,submit:14,submitted_personal_data:[3,10],submodul:[1,5],subpackag:1,successfulli:14,suggest:14,summar:10,support:14,survei:[10,14],syntact:14,system:10,tabl:10,tag:[3,10,13,14],taken:11,templat:6,templatetag:[1,2],termin:6,text:[7,8,10],textarea:10,than:10,thei:10,them:8,thi:[3,4,6,7,8,10,11,13,14],through:10,time:10,timestamp:[3,10],togeth:9,trail:7,translat:[8,9,10],treat:10,tupl:10,two:[10,14],type:[10,14],typic:10,unflag:3,unflag_com:3,uniqu:10,unord:10,unsav:10,unseri:10,updat:10,upper:10,url:13,url_exampl:13,url_root:13,usabl:10,use:[9,10],used:[10,14],useful:[6,10],user:[3,7,10,14],using:8,util:[6,7],valu:[3,7,10,14],vector:14,verbose_nam:4,verifi:7,view:[1,2],wai:10,were:[3,14],what:10,when:10,where:[10,14],whether:10,which:[6,10,14],whitespac:[7,10],whose:14,wide:4,without:14,word:10,word_count:10,work:14,would:[6,10],wrapper:10,write:[8,14],write_po_fil:9,written:[10,14],year:10,zero:14},titles:["Welcome to Malasakit\u2019s documentation!","pcari","pcari package","pcari.admin module","pcari.apps module","pcari.management package","pcari.management.commands package","pcari.management.commands.cleantext module","pcari.management.commands.makedbtrans module","pcari.management.commands.makemessages module","pcari.models module","pcari.signals module","pcari.templatetags package","pcari.templatetags.localize_url module","pcari.views module"],titleterms:{admin:3,app:4,cleantext:7,command:[6,7,8,9],content:[2,5,6,12],document:0,indic:0,localize_url:13,makedbtran:8,makemessag:9,malasakit:0,manag:[5,6,7,8,9],model:10,modul:[2,3,4,5,6,7,8,9,10,11,12,13,14],packag:[2,5,6,12],pcari:[1,2,3,4,5,6,7,8,9,10,11,12,13,14],signal:11,submodul:[2,6,12],subpackag:[2,5],tabl:0,templatetag:[12,13],view:14,welcom:0}})