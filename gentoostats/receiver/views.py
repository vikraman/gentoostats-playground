def receive(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Method != POST.')

    # accept and parse request
