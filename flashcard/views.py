from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .models import Categoria, Flashcard, Desafio, FlashcardDesafio
from django.contrib.messages import constants
from django.contrib import messages

def novo_flashcard(request):
    if not request.user.is_authenticated:
        return redirect('/usuarios/logar')
 
    if request.method == "GET":
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        flashcards = Flashcard.objects.filter(user = request.user)

        categoria_filtrar = request.GET.get('categoria')
        dificuldade_filtrar = request.GET.get("dificuldade")

        if categoria_filtrar:
            flashcards = flashcards.filter(categoria__id = categoria_filtrar)

        if dificuldade_filtrar:
            flashcards = flashcards.filter(dificuldade = dificuldade_filtrar)

        return render(request, 'novo_flashcard.html', {'categorias': categorias, 
                                                       'dificuldades': dificuldades, 
                                                       'flashcards': flashcards})
    
    elif request.method == "POST":
        pergunta = request.POST.get('pergunta')
        resposta = request.POST.get('resposta')
        categoria = request.POST.get('categoria')
        dificuldade = request.POST.get('dificuldade')

        if len(pergunta.strip()) == 0 or len(resposta.strip()) == 0:
            messages.add_message(request, constants.ERROR, "Os campos de pergunta e resposta devem estar preenchidos!")
            return redirect('/flashcard/novo_flashcard/')

    flashcard = Flashcard(
        user = request.user,
        pergunta = pergunta,
        resposta = resposta,
        categoria_id = categoria,
        dificuldade = dificuldade
    )
    flashcard.save()
    messages.add_message(request, constants.SUCCESS, "Seu Flashcrad foi cadastrado com sucesso.")
    return redirect('/flashcard/novo_flashcard/')

def deletar_flashcard(request, id):
    # Fazer a validação de segurança
    flashcard = Flashcard.objects.get(id = id)
    flashcard.delete()
    messages.add_message(request, constants.SUCCESS, 'Flashcard deletado com sucesso.')
    return redirect('/flashcard/novo_flashcard/')

def iniciar_desafio(request):
    if request.method == 'GET':
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        return render(request, 'iniciar_desafio.html', {'dificuldades': dificuldades, 'categorias': categorias})
    elif request.method == "POST":
        titulo = request.POST.get('titulo')
        categorias = request.POST.getlist('categoria')
        dificuldade = request.POST.get('dificuldade')
        qtd_perguntas = request.POST.get('qtd_perguntas')

        desafio = Desafio(
            user = request.user,
            titulo = titulo,
            dificuldade = dificuldade,
            quantidade_perguntas = qtd_perguntas
        )
        desafio.save()

        for categoria in categorias:
            desafio.categoria.add(categoria)
        
        flashcards = (
            Flashcard.objects.filter(user = request.user)
            .filter(dificuldade = dificuldade)
            .filter(categoria_id__in = categorias)
            .order_by('?')
        )
        
        if flashcards.count() < int(qtd_perguntas):
            # tratar para escolher depois
            return redirect('/flashcard/iniciar_desafio/')
        
        flashcards = flashcards[:int(qtd_perguntas)]

        for f in flashcards:
            flashcard_desafio = FlashcardDesafio(
                flashcard = f
            )
            flashcard_desafio.save()
            desafio.flashcards.add(flashcard_desafio)
        desafio.save()
        return redirect('/flashcard/listar_desafio/')

def listar_desafio(request):
    desafios = Desafio.objects.filter(user=request.user)
    # TODO: desenvolver os status
    # TODO: desenvolver os filtros
    return render(request,'listar_desafio.html', {'desafios': desafios})
        
def desafio(request, id):
    desafio = Desafio.objects.get(id = id)

    if request.method == "GET":
        acertos = desafio.flashcards.filter(respondido = True).filter(acertou = True).count()
        erros = desafio.flashcards.filter(respondido = True).filter(acertou = False).count()
        total = desafio.flashcards.filter(respondido = False).count()
        return render(request, 'desafio.html', {'desafio': desafio, 'acertos': acertos, 'erros': erros, 'total': total})
    

def responder_flashcard(request, id):
    flashcard_desafio = FlashcardDesafio.objects.get(id = id)
    acertou = request.GET.get('acertou')
    desafio_id = request.GET.get('desafio_id')

    if not flashcard_desafio.flashcard.user == request.user:
        raise Http404()

    flashcard_desafio.respondido = True

    flashcard_desafio.acertou = True if acertou == "1" else False

    flashcard_desafio.save()

    return redirect(f'/flashcard/desafio/{desafio_id}')

def relatorio(request, id):
    desafio = Desafio.objects.get(id = id)

    acertou = desafio.flashcards.filter(acertou = True).count()
    errou = desafio.flashcards.filter(acertou = False).count()
    dados = [acertou, errou]

    categorias = desafio.categoria.all()
    name_categoria = []

    for i in categorias:
        name_categoria.append(i.nome)

    dados2 = []

    for categoria in categorias:
        dados2.append(desafio.flashcards.filter(flashcard__categoria = categoria).filter(acertou = True).count())

    # TODO: Fazer o ranking
    return render(request, 'relatorio.html', {'desafio': desafio, 'dados': dados, 'categorias': name_categoria, 'dados2': dados2})


































































































































