from django.shortcuts import render, get_object_or_404, redirect
from blog.models import Post, Comment, Preference
from users.models import Follow, Profile
import sys
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from .forms import NewCommentForm
from django.contrib.auth.decorators import login_required
from .serializers import UserSerializer, GroupSerializer, PostSerializer
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from rest_framework import status
from django.template.defaulttags import register
from blog.SentimentalAnalysis import predict 

from blog.friend import *



def is_users(post_user, logged_user):
    return post_user == logged_user

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

PAGINATION_COUNT = 3
"""
class MutualListView(LoginRequiredMixin, ListView):
    
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = PAGINATION_COUNT

    def get_context_data(self, **kwargs):

        data = super().get_context_data(**kwargs)
        dict ={}
        mut = {}
        all_sugg = []
        logged_user = self.request.user.username
        users = User.objects.all()
        for x in users:
            dict[x.username] = [u.follow_user.username for u in Follow.objects.filter(user=x).all()]
        if dict[logged_user] != []:
            sugg_list, mutuals = friend(dict,logged_user,5) 
            for i in sugg_list:
                all_sugg.append(User.objects.get(username = i))
            for i in mutuals:
                mut[User.objects.get(username = i)]=[]
                for j in mutuals[i]:                
                    mut[User.objects.get(username = i)].append(User.objects.get(username = j))
        else:
            for i in range(1,6):
                all_sugg.append(User.objects.get(id = i))
        data['all_sugg'] = all_sugg
        data['mut'] = mut
        return data

    def get_queryset(self):
        user = self.request.user
        qs = Follow.objects.filter(user=user)
        follows = [user]
        friend={user.username : []}
        for obj in qs:
            #print("^^^^^^")
            friend[user.username].append(obj.follow_user.username)
            follows.append(obj.follow_user)
        #print(Follow.objects.filter(user=user).order_by('-date')[0].follow_user)
        print("1")
        print(friend)
       
        print(follows)
        return Post.objects.filter(author__in=follows).order_by('-date_posted')


"""


        

class PostListView(LoginRequiredMixin, ListView):
    
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = PAGINATION_COUNT

    def get_context_data(self, **kwargs):

        data = super().get_context_data(**kwargs)
        dict ={}
        all_sugg = []
        mut={}
        logged_user = self.request.user.username
        users = User.objects.all()
        for x in users:
            dict[x.username] = [u.follow_user.username for u in Follow.objects.filter(user=x).all()]
        sugg_list, mutuals = friend(dict,logged_user,5) 
        for i in sugg_list:
            all_sugg.append(User.objects.get(username = i))
            mut[User.objects.get(username = i)]=[]
            for j in mutuals[i]:                
                mut[User.objects.get(username = i)].append(User.objects.get(username = j))
        data['all_sugg'] = all_sugg
        print("--------------------")
        print(all_sugg)

        data['mut']=mut
        print("--------------------")
        print(mut)

        for i in mut:
            for j in mut[i]:
                print(j)

        return data

    def get_queryset(self):
        user = self.request.user
        qs = Follow.objects.filter(user=user)
        follows = [user]
        friend={user.username : []}
        for obj in qs:
            #print("^^^^^^")
            friend[user.username].append(obj.follow_user.username)
            follows.append(obj.follow_user)
        #print(Follow.objects.filter(user=user).order_by('-date')[0].follow_user)
        print("1")
        print(friend)
       
        print(follows)
        return Post.objects.filter(author__in=follows).order_by('-date_posted')





class UserPostListView(LoginRequiredMixin, ListView):
    model = Post

    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = PAGINATION_COUNT

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_context_data(self, **kwargs):
        visible_user = self.visible_user()
        logged_user = self.request.user
        print(logged_user.username == '', file=sys.stderr)

        if logged_user.username == '' or logged_user is None:
            can_follow = False
        else:
            can_follow = (Follow.objects.filter(user=logged_user,
                                                follow_user=visible_user).count() == 0)
        data = super().get_context_data(**kwargs)

        data['user_profile'] = visible_user
        data['can_follow'] = can_follow
        return data

    def get_queryset(self):
        user = self.visible_user()
        return Post.objects.filter(author=user).order_by('-date_posted')

    def post(self, request, *args, **kwargs):
        if request.user.id is not None:
            follows_between = Follow.objects.filter(user=request.user,
                                                    follow_user=self.visible_user())

            if 'follow' in request.POST:
                    new_relation = Follow(user=request.user, follow_user=self.visible_user())
                    if follows_between.count() == 0:
                        new_relation.save()
            elif 'unfollow' in request.POST:
                    if follows_between.count() > 0:
                        follows_between.delete()

        return self.get(self, request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comments_connected = Comment.objects.filter(post_connected=self.get_object()).order_by('-date_posted')
        data['comments'] = comments_connected
        data['form'] = NewCommentForm(instance=self.request.user)
        return data

    def post(self, request, *args, **kwargs):
        new_comment = Comment(content=request.POST.get('content'),
                              author=self.request.user,
                              post_connected=self.get_object())
        new_comment.save()

        return self.get(self, request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_delete.html'
    context_object_name = 'post'
    success_url = '/'

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['content']
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.sentiment = predict(str(self.request.POST.get("content")))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Add a new post'
        return data


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['content']
    template_name = 'blog/post_new.html'
    success_url = '/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.sentiment = predict(str(self.request.POST.get("content")))
        return super().form_valid(form)

    def test_func(self):
        return is_users(self.get_object().author, self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['tag_line'] = 'Edit a post'
        return data


class FollowsListView(ListView):
    print("-----------")
    print(ListView)
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        
        print(user.profile.followers )
        print("############")
        #print(Follow.objects.filter(user=user))
        
        print(Follow.objects.filter(user=user).order_by('-date')[1].follow_user)
        return Follow.objects.filter(user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow']='follows'
        
        return data


class FollowersListView(ListView):
    model = Follow
    template_name = 'blog/follow.html'
    context_object_name = 'follows'
    

    def visible_user(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        user = self.visible_user()
        return Follow.objects.filter(follow_user=user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(**kwargs)
        data['follow'] = 'followers'
        
        return data


# Like Functionality====================================================================================

@login_required
def postpreference(request, postid, userpreference):
        
        if request.method == "POST":
                eachpost= get_object_or_404(Post, id=postid)

                obj=''

                valueobj=''

                try:
                        obj= Preference.objects.get(user= request.user, post= eachpost)

                        valueobj= obj.value #value of userpreference


                        valueobj= int(valueobj)

                        userpreference= int(userpreference)
                
                        if valueobj != userpreference:
                                obj.delete()


                                upref= Preference()
                                upref.user= request.user

                                upref.post= eachpost

                                upref.value= userpreference


                                if userpreference == 1 and valueobj != 1:
                                        eachpost.likes += 1
                                        eachpost.dislikes -=1
                                elif userpreference == 2 and valueobj != 2:
                                        eachpost.dislikes += 1
                                        eachpost.likes -= 1
                                

                                upref.save()

                                eachpost.save()
                        
                        
                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')

                        elif valueobj == userpreference:
                                obj.delete()
                        
                                if userpreference == 1:
                                        eachpost.likes -= 1
                                elif userpreference == 2:
                                        eachpost.dislikes -= 1

                                eachpost.save()

                                context= {'eachpost': eachpost,
                                  'postid': postid}

                                return redirect('blog-home')
                                
                        
        
                
                except Preference.DoesNotExist:
                        upref= Preference()

                        upref.user= request.user

                        upref.post= eachpost

                        upref.value= userpreference

                        userpreference= int(userpreference)

                        if userpreference == 1:
                                eachpost.likes += 1
                        elif userpreference == 2:
                                eachpost.dislikes +=1

                        upref.save()

                        eachpost.save()                            


                        context= {'eachpost': eachpost,
                          'postid': postid}

                        return redirect('blog-home')


        else:
                eachpost= get_object_or_404(Post, id=postid)
                context= {'eachpost': eachpost,
                          'postid': postid}

                return redirect('blog-home')



def about(request):
    return render(request,'blog/about.html',)



class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]



@api_view(['GET', 'POST', 'DELETE'])
def post_list(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        
        title = request.query_params.get('title', None)
        if title is not None:
            posts = posts.filter(title__icontains=title)
        
        posts_serializer = PostSerializer(posts, many=True)
        return JsonResponse(posts_serializer.data, safe=False)
        # 'safe=False' for objects serialization
 
    elif request.method == 'POST':
        post_data = JSONParser().parse(request)
        post_serializer = PostSerializer(data=post_data)
        if post_serializer.is_valid():
            post_serializer.save()
            return JsonResponse(post_serializer.data, status=status.HTTP_201_CREATED) 
        return JsonResponse(post_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        count = Post.objects.all().delete()
        return JsonResponse({'message': '{} Posts were deleted successfully!'.format(count[0])}, status=status.HTTP_204_NO_CONTENT)
 