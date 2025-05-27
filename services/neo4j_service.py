# services/neo4j_service.py
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

class Neo4jService:
    def __init__(self, uri, user, password, database):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._database = database
        print(f"Neo4jService initialized for database: {database}")

    def close(self):
        if self._driver is not None:
            self._driver.close()
            print("Neo4j Driver closed.")

    def _execute_query(self, query, parameters=None):
        with self._driver.session(database=self._database) as session:
            results = session.run(query, parameters)
            return [record.data() for record in results]

    def get_recommended_recipes(self, recipe_name_query, category_query, mood_query):
        params = {
            "recipeNameQuery": recipe_name_query if recipe_name_query else "",
            "categoryQuery": category_query if category_query else "",
            "moodQuery": mood_query if mood_query else ""
        }
        query = (
            "MATCH (r:Recipe) "
            "OPTIONAL MATCH (r)-[:BELONGS_TO_CATEGORY]->(c:Category) "
            "OPTIONAL MATCH (r)-[:SUITS_MOOD]->(m:Mood) "
            "WITH r, collect(DISTINCT c.name) AS categories, collect(DISTINCT m.name) AS moods "
            "WHERE ($recipeNameQuery = '' OR r.name CONTAINS $recipeNameQuery) " # 或者使用更精確的 r.clean_name (如果您有這個屬性)
            "  AND ($categoryQuery = '' OR $categoryQuery IN categories) "
            "  AND ($moodQuery = '' OR $moodQuery IN moods) "
            "RETURN r.name AS recipeName, "
            "       r.description_for_recommendation AS recommendationDescription, "
            "       r.difficulty_stars AS difficultyStars, "
            "       r.image_url AS imageUrl " # 假設 imageUrl 是您用於推薦列表的本地圖片路徑
            "LIMIT 20"
        )
        return self._execute_query(query, params)


    def get_recipe_details(self, recipe_name):
        params = {"recipeName": recipe_name} # 假設 recipe_name 是純菜名
        query = (
            "MATCH (r:Recipe {name: $recipeName}) " # 或者使用 r.clean_name
            "RETURN "
            "    r.name AS recipeName, "
            "    r.difficulty_stars AS difficultyStars, "
            "    r.difficulty_text AS difficultyText, "
            "    r.required_items_text AS requiredItemsText, "
            "    r.calculations_text AS calculationsText, "
            "    r.notes_text AS notesText, "
            "    r.source_file AS sourceFile"
        )
        result = self._execute_query(query, params)
        return result[0] if result else None

    def get_recipe_steps(self, recipe_name):
        """
        根據食譜名稱獲取所有操作步驟，按順序排列。
        現在會包含音訊路徑。
        """
        params = {"recipeName": recipe_name} # 假設 recipe_name 是純菜名
        # --- 修改 RETURN 子句 ---
        query = (
            "MATCH (r:Recipe {name: $recipeName})-[:FIRST_STEP]->(first_step:Step) " # 或者使用 r.clean_name
            "MATCH path = (first_step)-[:NEXT_STEP*0..]->(any_step:Step) "
            "WITH any_step "
            "ORDER BY any_step.order ASC " # 確保是 ASC
            "RETURN "
            "    any_step.order AS stepOrder, "
            "    any_step.instruction AS stepInstruction, "
            "    any_step.animationCue AS animationCue, " # 保留 animationCue
            "    any_step.audioPathMandarin AS audioPathMandarin, " # <--- 新增
            "    any_step.audioPathTaiwanese AS audioPathTaiwanese" # <--- 新增
        )
        # -----------------------
        return self._execute_query(query, params)

# 建立 Neo4jService 的單一實例
neo4j_service_instance = Neo4jService(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)

def close_neo4j_on_exit():
    print("Closing Neo4j connection from neo4j_service...")
    neo4j_service_instance.close()