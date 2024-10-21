import functools, time
from neo4j import GraphDatabase, ManagedTransaction, exceptions
from rid_lib.core import RID
from .utils import rid_params


class GraphInterface:
    def __init__(self, uri, auth, db):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.db = db
        
        while True:
            try:
                self.driver.verify_connectivity()
                print("connected to Neo4j server")
                break
            except exceptions.ServiceUnavailable:
                print("Failed to connect to Neo4j server, retrying...")
                time.sleep(5)
                
    # Wrapper functions for performing Neo4j Cypher operations
    def execute_read(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.driver.session(database=self.db) as session:
                return session.execute_read(func, *args, **kwargs)
        return wrapper

    def execute_write(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.driver.session(database=self.db) as session:
                return session.execute_write(func, *args, **kwargs)
        return wrapper
    
    def read_all(self):
        @self.execute_read
        def execute_read_all(tx: ManagedTransaction):
            READ_ALL = """//cypher
                MATCH (object:message) RETURN collect(object.rid) AS objects
                """
            
            record = tx.run(READ_ALL).single()
            if record:
                return [
                    RID.from_string(obj) for obj in record["objects"]
                ]
        
        return execute_read_all()
                
    def create(self, rid: RID):
        """Creates a new RID graph object."""
        @self.execute_write
        def execute_create(tx: ManagedTransaction):
            labels = f"{rid.space}:{rid.form}"

            CREATE_OBJECT = f"""//cypher
                MERGE (object:{labels} {{rid: $rid}})
                SET object += $params
                RETURN object
                """

            tx.run(
                CREATE_OBJECT,
                rid=str(rid),
                params=rid_params(rid)
            )

        return execute_create()

    def create_link(self, source: RID, target: RID, tag: str) -> bool:
        """Creates a new link RID graph object."""
        @self.execute_write
        def execute_create(tx: ManagedTransaction, source, target, tag):
            CREATE_LINK = """//cypher
                MATCH (source {rid: $source_rid})
                MATCH (target {rid: $target_rid})
                MERGE (source)-[link:LINK {tag: $tag}]->(target)
                RETURN link
                """

            record = tx.run(
                CREATE_LINK, 
                source_rid=str(source), 
                target_rid=str(target),
                tag=tag
            ).single()
            
            return record is not None
        
        return execute_create(source, target, tag)
    
    def delete(self, rid: RID):
        """Deletes RID graph object."""
        @self.execute_write
        def execute_delete(tx: ManagedTransaction):
            DELETE_OBJECT = """//cypher
                MATCH (object {rid: $rid})
                DETACH DELETE object
                RETURN object
                """
            
            record = tx.run(DELETE_OBJECT, rid=str(rid)).single()
            return record is not None
        
        return execute_delete()
    
    def drop(self):
        """Deletes all graph objects."""
        @self.execute_write
        def execute_drop(tx: ManagedTransaction):
            DROP_DATABASE = """//cypher
                MATCH (n) DETACH DELETE n
                """
            
            tx.run(DROP_DATABASE)
        
        return execute_drop()