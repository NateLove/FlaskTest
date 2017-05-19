from flask import Flask
from flask_restplus import Api, Resource, fields
from pymongo import MongoClient

client = MongoClient()
db = client.test

app = Flask(__name__)
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
)

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readOnly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'description': fields.String(required=False, description='The task description'),
    'complete': fields.Boolean(required=False, description='Completion status', default=False)
})


class TodoDAO(object):
    def __init__(self, db):
        self.db = db
        self.todos = []
        self.counter = 0
        for doc in self.db.tasks.find():
            self.todos.append(doc)

        for doc in self.db.counter.find():
            self.counter = doc['count']

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        todo['id'] = self.get_counter()
        todo['complete'] = False
        self.todos.append(todo)
        self.db.tasks.insert_one(todo)
        return todo

    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        self.db.tasks.update_one(
        { 'id': id},
        {"$set":data}
        )
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)
        self.db.tasks.delete_many({'id':id})

    def get_complete(self):
        complete = []
        for todo in self.todos:
            if todo['complete']:
                complete.append(todo)

        return complete

    def get_not_complete(self):
        not_complete = []
        for todo in todos:
            if not todo['complete']:
                not_complete.append(todo)

        return not_complete

    def get_counter(self):
        self.counter += 1
        self.db.counter.update_one(
        {'id':'counter'},
        {"$set": {'id':'counter','count':self.counter}},
        upsert=True
        )
        return self.counter - 1

    def complete(self, id):
        todo = self.get(id)
        for todo in self.todos:
            if todo['id'] == id:
                if todo['complete']:
                    api.abort(400, "Todo {} is already complete".format(id))
                todo['complete'] = True
        self.db.tasks.update_one(
        { 'id': id},
        {"$set": {'complete':True}}
        )
        return todo


DAO = TodoDAO(db.tasks)


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_list_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)

@ns.route('/complete/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', "The task identifier")
class TodoCompleted(Resource):
    '''View completed todos and mark uncompleted todos as complete'''
    @ns.marshal_with(todo, code=201)
    @ns.doc('complete_todo')
    def put(self,id):
        '''Mark task as complete'''
        return DAO.complete(id), 201

@ns.route('/complete/')
class TodoComplete(Resource):
    '''Shows a list of all complete todos'''
    @ns.doc('list_complete_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.get_complete()


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
