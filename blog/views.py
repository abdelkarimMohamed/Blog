from django.shortcuts import render, get_object_or_404
from .models import Post
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger 
from django.views.generic import ListView
from django.core.mail import send_mail
from .forms import EmailPostForm,CommentForm,SearchForm
from django.conf import settings
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


# from django.http import Http404

def post_list(request,tag_slug=None):

    post_list=Post.objects.all()

    tag=None

    if tag_slug:

        tag=get_object_or_404(Tag,slug=tag_slug)
        post_list=post_list.filter(tags__in=[tag])  
        # post_list=post_list.filter(tags__slug__in=[tag])
  

    paginator = Paginator(post_list, 2)
    page_number = request.GET.get("page",1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger: 
        posts = paginator.page(1)

    return render(request,'blog/post/list.html',{'posts':posts,'tag':tag})

# class PostListView(ListView):
#     model=Post
#     context_object_name='posts'
#     paginate_by=2
#     template_name='blog/post/list.html'

def post_detail(request,year,month,day,post):

    post=get_object_or_404(Post, status=Post.Status.PUBLISHED,
                           slug=post,
                           publish__year=year,
                           publish__month=month,
                           publish__day=day,
                           )
    comments=post.comments.filter(active=True)
    form=CommentForm()

    tags_posts=post.tags.values_list('id',flat=True)

    similar_posts=Post.objects.filter(tags__in=tags_posts).exclude(id=post.id)  
    similar_posts=similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')

    return render(request,'blog/post/detail.html',{'post':post,'form':form,'comments':comments,'similar_posts':similar_posts})


def post_share(request,post_id):
     
    post = get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':

        form=EmailPostForm(request.POST)
        if form.is_valid():

            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url} \n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'abdelkarimmohamedali81@gmail.com', [cd['to']])

            sent=True
    else:
         form=EmailPostForm()
    return render(request,'blog/post/share.html',{'post':post,'form':form,'sent':sent})

@require_POST
def post_comment(request,post_id):
    post = get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    comment=None

    form=CommentForm(data=request.POST)
    if form.is_valid():
        comment=form.save(commit=False)

        comment.post=post
        comment.save()

    return render(request,'blog/post/comment.html',{'post':post,'comment':comment,'form':form})

def post_search(request):

    form=SearchForm()
    query=None
    results=[]

    if 'query' in  request.GET:

        form=SearchForm(request.GET)
        if form.is_valid():
            query=form.cleaned_data['query']
            search_vector=SearchVector('title','body')
            search_query=SearchQuery(query, config='english') #improve query find origin word 
            # results = Post.objects.annotate(search=SearchVector('title','body')).filter(search=query)
            # searchRank => return important result and orderby inverse
            results = Post.objects.annotate(search=search_vector, rank=SearchRank(search_vector, search_query)).filter(search=search_query).order_by('-rank') 
    return render(request,'blog/post/search.html',{'form': form,'query': query,'results': results})

