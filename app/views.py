# Create your views here.

from _codecs import register
from datetime import date
from os import listdir
import re
import urllib2

from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from django.forms.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from pattern.db import date
from pattern.web    import Newsfeed, plaintext, strip_between
from whoosh import index
from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh.qparser import plugins
from whoosh.qparser.default import MultifieldParser, QueryParser
from whoosh.query.compound import And, Or
from whoosh.query.qcore import Every
from whoosh.query.terms import Term

from app.models import IngresoForm, Usuario, Periodico


def home(request):
    if not 'us_id' in request.session:
        news, url = {}, 'http://news.google.com/news?output=rss'
        #url = 'http://news.google.com/news?output=rss'
        dic = {}
        for story in Newsfeed().search(url, cached=False):
            d = str(date(story.date, format='%Y-%m-%d'))
            titulo = plaintext(story.title)
            des = plaintext(story.description)
            
            #evitar contenido duplicado
            news.setdefault(d, {})[hash(des)] = des       
            dic[titulo] = [des,d];
           
    else:
        return HttpResponseRedirect("/noticias")
    
    return render_to_response('home.html',{'dic':dic}, context_instance= RequestContext(request))



def squema():
    schema= Schema(nombre_periodico= TEXT(stored=True),
                titulo= TEXT(stored=True),
                resumen=TEXT(stored=True),
                categoria=TEXT(stored=True),
                imagen= TEXT(stored=True),
                enlace=TEXT(stored= True))
    
    ix = create_in("indexado", schema)
    writer = ix.writer()
    return writer

 
 
 
def nuevo_usuario(request):
    if 'us_id' in request.session:
        return HttpResponseRedirect('/noticias')
    else:
        if request.method=='POST':
            formulario= IngresoForm(request.POST)
            if formulario.is_valid():
                formulario.save()
                m = Usuario.objects.get(nombre=request.POST['nombre'])
                request.session['us_id'] = m.id
                return HttpResponseRedirect('/noticias')
        else:
            formulario= IngresoForm()
    return render_to_response('register.html', {'formulario': formulario}, context_instance= RequestContext(request))


    
def login(request):
    if 'us_id' in request.session:
        return HttpResponseRedirect('/noticias')
    else:
        usuario = '';
        try:
            if request.method=='POST':
                formulario= IngresoForm(request.POST)
                if formulario.is_valid:
                    m = Usuario.objects.get(nombre=request.POST['nombre'])
                    usuario = request.POST['nombre']
                    if m.contrasena == request.POST['contrasena']:
                        request.session['us_id'] = m.id
                        return HttpResponseRedirect('/noticias')
                    else:
                        return render_to_response('login.html', {'formulario': formulario,'msg':'Usuario o contrasena incorrectos'},context_instance= RequestContext(request))
            else:
                formulario= IngresoForm()
        except Usuario.DoesNotExist:
            return render_to_response('login.html', {'formulario': formulario,'msg':'Usuario o contrasena incorrectos'},context_instance= RequestContext(request))
    
    return render_to_response('login.html', {'formulario': formulario},context_instance= RequestContext(request))
    
    

        
def logout(request):
    try:
        del request.session['us_id']
    except KeyError:
        pass
    return HttpResponseRedirect('/home')
    


def noticias(request):
    
    if 'us_id' in request.session:
        usuario = getUsuario(request)
        periodicos={};
        periodicos_favoritos = usuario.periodico
        busqueda=""
        p = ""
        cat = ""
        per = ""
        #formulario de busqueda
        if request.method =='POST':
                      
            busqueda= request.POST['consulta']
            per = request.POST['filtro_periodicos']
            cat = request.POST['filtro_categoria']
            
            if busqueda =="" and per =="" and cat=="":
                return HttpResponseRedirect("/noticias")
            else:  
                ix = index.open_dir('indexado')
                
                if busqueda !="":
                    cn=busqueda.split()
                    ##
                    archivo=open("midiccionario.txt","r")
                    lectArchivo= archivo.readlines()
                    if len(cn) != 0:
                        for elemento in cn: 
                            for li in lectArchivo: 
                                if li.rstrip('\n')==elemento.rstrip('\n'):
                                    cn.remove(elemento)
                    ## 
                    consulta = cn[0] + ''.join([" AND " + elemento  for elemento in cn[1:]])       
                else:
                    consulta = busqueda
                    
                with ix.searcher() as searcher:
                    ##
                    qp = MultifieldParser(["titulo", "resumen"], ix.schema)
                    qp.add_plugin(plugins.FieldAliasPlugin({"nombre_periodico":('periodico'),"categoria":('categoria')}))
                    
                    if busqueda !="" and per =="" and cat=="":
                        query = qp.parse(consulta)
                         
                    elif busqueda =="" and per !="" and cat=="":
                        
                        query = qp.parse(" nombre_periodico:"+per)
                          
                    elif busqueda =="" and per =="" and cat!="":
                       
                        query = qp.parse(" categoria:'"+cat+"'")
                    elif busqueda !="" and per !="" and cat=="":
                        
                        query = qp.parse(consulta+" nombre_periodico:"+per)
                    elif busqueda =="" and per !="" and cat!="":
                        
                        query = qp.parse(" nombre_periodico:"+per+" categoria:'"+cat+"'")
                    elif busqueda !="" and per =="" and cat!="":
                        
                        query = qp.parse(consulta+" categoria:"+cat)
                    elif busqueda !="" and per !="" and cat!="":
                       
                        query= qp.parse(consulta+" nombre_periodico:"+per+" categoria:'"+cat+"'")
                        
                    resultado = searcher.search(query)
                    for r in resultado:     
                        if unicode(r['nombre_periodico']) in periodicos.keys():
                            noticias = periodicos[unicode(r['nombre_periodico'])]
                        else:
                            noticias = {}
                            
                        noticias[unicode(r['titulo'])] = [unicode(r['enlace']),unicode(r['resumen']),unicode(r['imagen'])]
                        periodicos[unicode(r['nombre_periodico'])] = noticias           
                
        
        #formulario de filtro    
        
        else:        
            url = {'PAIS':'http://ep00.epimg.net/rss/elpais/portada.xml','MUNDO':'http://estaticos.elmundo.es/elmundo/rss/portada.xml', 'ABC':'http://www.abc.es/rss/feeds/abcPortada.xml'}
            writer=squema()
            indice=0
            indice1=0
            lista_abc=[] 
            imagenes_lista_mundo=[] 
            for key in url.keys():
                str_img=""
                flag=1
                flag1=1
                noticias = {} 
                for result in Newsfeed().search(url[key],tags=['description', 'title', 'link','category','enclosures'], cached=False):
                    
                    titulo = plaintext(result.title)
                    ##
                    if key == "PAIS":            
                        try:
                            indixe= result.enclosures.index(".jpg")
                            str_img=result.enclosures[31:indixe+4] 
                            
                            writer.add_document(nombre_periodico= unicode(key),
                                titulo= unicode(plaintext(result.title)),
                                resumen= unicode(" ".join(plaintext(result.description).split()).replace("Seguir leyendo."," ")),
                                categoria=unicode(plaintext(result.category)),
                                imagen=unicode(str_img),
                                enlace=unicode(plaintext(result.link))) 
                        except ValueError:
                            str_img ="nada"
                        descripcion = plaintext(result.description)
                        lista = [str(plaintext(result.link)),descripcion,str_img]
                           
                    if key =="MUNDO":
                        soup = BeautifulSoup(urllib2.urlopen(url[key])) 
                        if flag==1:   
                            for i in soup.find_all("item"):
                                imagen=i.find("media:content")
                                if imagen!=None:
                                    imagenes_lista_mundo.append(imagen['url'])
                                else:
                                    imagen="nada"
                                    imagenes_lista_mundo.append(imagen)
                                
                            flag=0
                        descripcion = plaintext(result.description)       
                        lista = [str(plaintext(result.link)),descripcion,imagenes_lista_mundo[indice1]]       
                        writer.add_document(nombre_periodico= unicode(key),
                            titulo= unicode(plaintext(result.title)),
                            resumen= unicode(" ".join(plaintext(result.description).split()).replace("Seguir leyendo."," ")),
                            categoria=unicode(plaintext(result.category)),
                            imagen=unicode(imagenes_lista_mundo[indice1]),
                            enlace=unicode(plaintext(result.link))) 
                        indice1= indice1 + 1 
                        
                    
                    if key == "ABC":
                        soup = BeautifulSoup(urllib2.urlopen(url[key]))
                        if flag1==1:
                            for i in soup.find_all("description"):   
                                eti= i.next_element
                                cont=0
                                for l in re.findall(r'\s*<img align="left" src="(.*).jpg|.JPG">',eti):
                                    if l!="":
                                        imageNoti= l + ".jpg"
                                        lista_abc.append(imageNoti)
                                    else:
                                        li_aux=re.findall(r'\s*<img align="left" src="(.*).JPG">', eti)
                                        imageNoti=li_aux[cont]+ ".jpg"
                                        lista_abc.append(imageNoti)
                                        cont+=1
                            flag1=0 
                        descripcion = plaintext(result.description)       
                        lista = [str(plaintext(result.link)),descripcion,lista_abc[indice]] 
                        
                        writer.add_document(nombre_periodico= unicode(key),
                            titulo= unicode(plaintext(result.title)),
                            resumen= unicode(" ".join(plaintext(result.description).split()).replace("Seguir leyendo."," ")),
                            categoria=unicode(plaintext(result.category)),
                            imagen=unicode(lista_abc[indice]),
                            enlace=unicode(plaintext(result.link))) 
                        indice= indice + 1           
                    
                    noticias[titulo] = lista
                ##      
                for periodico in periodicos_favoritos.all():
                    if str(key) == str(periodico):
                        periodicos[key] = noticias
            writer.commit()      
            
        ix = index.open_dir("indexado")
        categorias_Disponibles=[]
        with ix.searcher() as searcher:
            for l in list(searcher.documents()):
                for k in l.keys():
                    if k == "categoria":
                        if not l[k]=="":
                            categorias_Disponibles.append(l[k])
            categorias_Disponibles=list(set(categorias_Disponibles))
        return render_to_response('news.html',{'cat':cat,'per':per,'busqueda':busqueda,'periodicos':periodicos,'usuario': usuario,'categorias':categorias_Disponibles},context_instance = RequestContext(request))
    else:
        return HttpResponseRedirect("/home")
    
def profile(request):
    if 'us_id' in request.session:
        usuario = getUsuario(request)
        if request.method=='POST':
            form = IngresoForm(request.POST)
            if form.is_valid():
                nombre = request.POST['nombre']
                contrasena = request.POST['contrasena']
                email = request.POST['email']
                periodico = request.POST['periodico']
                usuario.nombre = nombre
                usuario.contrasena = contrasena
                usuario.email = email
                usuario.periodico = periodico
                usuario.save()
                return HttpResponseRedirect("/home")
            else:
                return HttpResponseRedirect("/perfil")
        else:
            form = IngresoForm()
            
    else:
        return HttpResponseRedirect("/home")
    
    return render_to_response('profile.html',{'formulario':form,'usuario':usuario},context_instance = RequestContext(request))



                 

##
def getUsuario(request):
    id_u = request.session['us_id'] 
    usuario = Usuario.objects.get(id=id_u)
    return usuario

 

