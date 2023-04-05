import psycopg2

import uuid

from slugify import slugify 
from datetime import datetime

from chalicelib import parser
from chalicelib.app import app
from chalicelib.secret_interface import get_credentials_database

def get_connection():
    credencial = get_credentials_database()

    password = credencial["password"]
    dbname = credencial["dbname"]
    username = credencial["user"]
    hostname = credencial["hostname"]

    conn = psycopg2.connect(
        f"dbname={dbname} user={username} "
        f"password={password} host={hostname}"
    )
    cursor = conn.cursor()
    return conn, cursor


def return_taxonomies():
    sql_all_taxonomy_return = """
        select tax.taxonomy_id, tax.name, tax.slug,  tax.active 
        from "content".taxonomies tax
        where tax.parent_id is null
        ORDER BY tax."name";
    """
    all_taxonomies = []

    try:         
        conn, cursor = get_connection()
        cursor.execute(sql_all_taxonomy_return)
        all_taxonomies_list = cursor.fetchall()
        app.log.info(f'{cursor.rowcount} taxonomias encontradas no PostgreSQL')

        for taxonomy_item in all_taxonomies_list:
                    
            taxonomy_item_obj = {
                'taxonomy_id': taxonomy_item[0],
                'taxonomy_name': taxonomy_item[1],
                'taxonomy_slug': taxonomy_item[2],
                'active': taxonomy_item[3]
            }
            all_taxonomies.append(taxonomy_item_obj)        

        cursor.close()
        conn.close()

        app.log.info('Taxonomies encontradas com sucesso!')
        return all_taxonomies, {'message': "Taxonomies encontradas com sucesso!", 'status_code': 200}
        
    except Exception as ex:
        app.log.error(f"Problemas ao retornar a lista de pastas. Error: {ex}")
        return None, {'message': f"Problemas ao retornar a lista de pastas. Error: {ex}", 'status_code': 500}

def return_taxonomy(taxonomy_id):

    sql_taxonomy_return = """
        SELECT taxonomies."name", taxonomies.slug, taxonomies.taxonomy_id, taxonomies.active, 
        taxonomies.parent_taxon_name, taxonomies.parent_taxon_slug, parent_taxon_id, parent_taxon_active, taxgroup.group_id, auth.author_id, 
        auth.name, auth.active, authdescr.description, tp.product_id, taxonomies.link, taxonomies.telegram_url, taxonomies.instagram_url, taxonomies.vitreo_label, taxonomies.vitreo_link, taxonomies.vitreo_link_type, taxonomies.vitreo_app_link, taxonomies.large_cover, taxonomies.small_cover, taxonomies.custom_avatar
        from (SELECT taxon."name", taxon.taxonomy_id, taxon.slug, taxon.active, parent_taxon."name" 
        AS parent_taxon_name, parent_taxon.slug AS parent_taxon_slug, parent_taxon.taxonomy_id AS parent_taxon_id, parent_taxon.active as parent_taxon_active, taxon.link, taxon.telegram_url, taxon.instagram_url, taxon.vitreo_label, taxon.vitreo_link, taxon.vitreo_link_type, taxon.vitreo_app_link, taxon.large_cover, taxon.small_cover, taxon.custom_avatar
        from content.taxonomies taxon LEFT JOIN content.taxonomies parent_taxon ON taxon.parent_id = parent_taxon.taxonomy_id) AS taxonomies
        left join "content".taxonomies_groups taxgroup
        on taxgroup.taxonomy_id = taxonomies.taxonomy_id
        left join "content".taxonomies_authors taxauth
        on taxauth.taxonomy_id = taxonomies.taxonomy_id
        left join "content".authors_descriptions authdescr
        on taxauth.author_description_id = authdescr.author_description_id 
        left join "content".authors auth
        on taxauth.author_id = auth.author_id
        left join "content".taxonomies_products tp 
        on taxonomies.taxonomy_id = tp.taxonomy_id
        where taxonomies.taxonomy_id = %s
        limit 1;
    """

    try:

        conn, cursor = get_connection()
        cursor.execute(sql_taxonomy_return, (taxonomy_id,))
        taxonomy_list = cursor.fetchall()         
        app.log.info(f'Buscando dados de taxonomia: {taxonomy_id}')

        if taxonomy_list:   
            
            for taxonomy_item in taxonomy_list:

                taxonomy_name, taxonomy_slug, taxonomy_id, taxonomy_active, taxonomy_parent_name, taxonomy_parent_slug, taxonomy_parent_id, taxonomy_parent_active, taxonomy_group_id, author_id, author_name, author_active, author_description, product_id, link, telegram_url, instagram_url, vitreo_label, vitreo_link, vitreo_link_type, vitreo_app_link, large_cover, small_cover, custom_avatar = taxonomy_item
                
                author_photo = None
                if author_name:
                    author_photo = f'https://cdn-publifiles-publicacoes.empiricus.com.br/static/authors/{slugify(author_name)}.jpg'

                author_obj = {
                    'author_id': author_id,
                    'name': author_name,
                    'active': author_active,
                    'avatar': author_photo,
                    'role': author_description
                }
                app.log.info(f'Author dictionary created')

                taxonomy_obj = {
                    'taxonomy_id': taxonomy_id,
                    'taxonomy_name': taxonomy_name,
                    'taxonomy_slug': taxonomy_slug,
                    'group_id': taxonomy_group_id,
                    'product_id': product_id,
                    'active': taxonomy_active,
                    'link': link, 
                    'telegram_url': telegram_url,
                    'instagram_url': instagram_url,
                    'vitreo_label': vitreo_label,
                    'vitreo_link': vitreo_link,
                    'vitreo_link_type': vitreo_link_type,
                    'vitreo_app_link': vitreo_app_link,
                    'large_cover': large_cover,
                    'small_cover': small_cover,
                    'custom_avatar': custom_avatar,
                    'author' : author_obj, 
                    'root': { 
                        "taxonomy_id": taxonomy_parent_id,
                        "taxonomy_name": taxonomy_parent_name,
                        "slug": taxonomy_parent_slug,
                        "active": taxonomy_parent_active,
                        "author": author_obj
                    }
                }
                app.log.info(f'taxonomy dictionary created')
                
        cursor.close()
        conn.close()

        app.log.info('Sucesso ao retornar os dados pasta.')
        return taxonomy_obj, {'message': "Sucesso ao retornar os dados pasta.", 'status_code': 200}                    

    except Exception as ex:
        app.log.info(f"Problemas ao retornar os dados pasta. Error: {ex}")
        return None, {'message': f"Problemas ao retornar os dados pasta. Error: {ex}", 'status_code': 500}
        
def return_child_list(taxonomy_id):
    
    sql_taxonomy_id_validation = """
        Select tax.taxonomy_id, tax.name, tax.active, tax.parent_id, tax.value
        from "content".taxonomies tax
        where tax.taxonomy_id = %s
    """

    sql_taxonomy_parent_id_return = """
        Select tax.value, tax.active, tax.taxonomy_id, tax.name, tax.slug, tax.parent_id, tax.created_at  
        from "content".taxonomies tax
        where tax.parent_id = %s
    """

    sql_publication_parent_id_return = """
        Select pub.value, pub.active, pub.publication_id , pub.title, pub.slug, pub.taxonomy_id, cont.content_type_id, pub.created_at
        from "content".publications pub
        inner join "content".taxonomies tax
        on pub.taxonomy_id = tax.taxonomy_id
        inner join "content".publications_contents pubcont 
        on pub.publication_id  = pubcont.publication_id 
        inner join "content".contents cont
        on cont.content_id  = pubcont.content_id 
        where pub.taxonomy_id = %s
        order by pub.release_date desc
    """
    data = []

    try:
        conn, cursor = get_connection()
        cursor.execute(sql_taxonomy_id_validation, (taxonomy_id,))
        count_row = cursor.rowcount
        app.log.info(f'Buscando dados de taxonomia e publicações de taxonomia root: {taxonomy_id}')

        if count_row > 0:
            taxonomy_list = cursor.fetchall()

            for taxonomy_item in taxonomy_list:
                cursor.execute(sql_taxonomy_id_validation, (taxonomy_item[3],))
                count_row = cursor.rowcount

                if count_row > 0:
                    root_list = cursor.fetchall()
                    
                    for root_item in root_list:

                        root_obj = {
                            "taxonomy_id": root_item[0],
                            "taxonomy_name": root_item[1],
                            "slug": slugify(root_item[1]),
                            "active": root_item[2]
                        }

                        taxonomy_obj = {
                            "taxonomy_id": taxonomy_item[0],
                            "taxonomy_name": taxonomy_item[1],
                            "slug": slugify(taxonomy_item[1]),
                            "active": taxonomy_item[2],
                            'item_order': taxonomy_item[4],
                            "root": root_obj
                        }
                        
                else: 
                    taxonomy_obj = {
                        "taxonomy_id": taxonomy_item [0],
                        "taxonomy_name": taxonomy_item [1],
                        "slug": slugify(taxonomy_item[1]),
                        "active": taxonomy_item[2],
                        'item_order': taxonomy_item[4],
                        "root": {
                            "taxonomy_id": None,
                            "taxonomy_name": None,
                            "slug": None,
                            "active": None
                        }        
                    }

            cursor.execute(sql_taxonomy_parent_id_return, (taxonomy_id,))
            count_row = cursor.rowcount
            app.log.info(f'Buscando dados de taxonomy_children no PostgreSQL')
        
            if count_row > 0:
                taxonomy_child_list = cursor.fetchall()
                
                for taxonomy_child_item in taxonomy_child_list:
                    
                    taxonomy_child_obj = {
                        "item_order": taxonomy_child_item[0],
                        "active": taxonomy_child_item[1],
                        "taxonomy_id": taxonomy_child_item[2],
                        "taxonomy_name": taxonomy_child_item[3],
                        "taxonomy_slug": taxonomy_child_item[4],
                        "parent_id": taxonomy_child_item[5],
                        "created_at": int(taxonomy_child_item[6].timestamp()),
                        "type" : "taxonomy"
                    }

                    data.append(taxonomy_child_obj)

            cursor.execute(sql_publication_parent_id_return, (taxonomy_id,))
            count_row = cursor.rowcount

            if count_row > 0:
                publication_child_list = cursor.fetchall()

                for publication_item in publication_child_list:

                    publication_child_obj = {
                        "item_order": publication_item[0],
                        "active": publication_item[1],
                        "publication_id": publication_item[2],
                        "title": publication_item[3],
                        "slug": publication_item[4],
                        "taxonomy_id": publication_item[5],
                        "content_type_id": publication_item[6],
                        "created_at": int(publication_item[7].timestamp()),
                        "type": "publication"
                    }
                    data.append(publication_child_obj)

        taxonomy_childrens = {
            "taxonomy": taxonomy_obj,
            "data": data
        }

        cursor.close()
        conn.close()

        app.log.info('Sucesso ao retornar os dados pasta.')
        return taxonomy_childrens, {'message': "Sucesso ao retornar os dados pasta.", 'status_code': 200}
            
    except Exception as ex:
        app.log.info(f"Problemas ao retornar os dados pasta. Error: {ex}")
        return None, {'message': f"Problemas ao retornar os dados pasta. Error: {ex}", 'status_code': 500}


def validate_new_taxonomy(new_taxonomy, user_id):
    try:

        taxonomy = {
            'taxonomy_id': str(uuid.uuid4()),
            'created_by': user_id,
            'created_at': datetime.now(),
        }

        sql_validate_parent_id = """
            SELECT taxonomy.parent_id
            FROM "content".taxonomies AS taxonomy
            WHERE taxonomy.taxonomy_id = %s AND taxonomy.parent_id IS NOT NULL;
        """
        if 'parent_id' in new_taxonomy:

            conn, cursor = get_connection()
            app.log.info(f"Validando parent_id: {new_taxonomy['parent_id']}")
            cursor.execute(sql_validate_parent_id, (new_taxonomy['parent_id'],))
            parent_id_result_rows = cursor.rowcount
            
            cursor.close()
            conn.close()

            if parent_id_result_rows:
                app.log.error(f"parent_id: {new_taxonomy['parent_id']} é invalido.")
                return None, {'message': f"Parente_id {new_taxonomy['parent_id']} invalido.", 'status_code': 400}

            else:
                taxonomy['parent_id'] = new_taxonomy['parent_id']
        else: 
            taxonomy['parent_id'] = None
            
        sql_validate_slug = """
            SELECT taxonomy.slug
            FROM "content".taxonomies AS taxonomy
            WHERE taxonomy.slug = %s;
        """
        if 'taxonomy_slug' in new_taxonomy:
            
            conn, cursor = get_connection()
            app.log.info(f"Verificando Slug: {new_taxonomy['taxonomy_slug']}")
            cursor.execute(sql_validate_slug, (new_taxonomy['taxonomy_slug'],))
            slugs_result_rows = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            if slugs_result_rows:
                app.log.error(f"Slug {new_taxonomy['taxonomy_slug']} já existe no banco de dados.")
                return None, {'message': f"Slug {new_taxonomy['taxonomy_slug']} já existe no banco de dados.", 'status_code': 400}
            
            else:
                taxonomy['taxonomy_slug'] = new_taxonomy['taxonomy_slug']
        else:
            app.log.error(f"É necessario informar o Slug.")
            return None, {'message': "É necessario informar o Slug", 'status_code': 400}

        if "taxonomy_name" in new_taxonomy:
            taxonomy['taxonomy_name'] = new_taxonomy['taxonomy_name']
        else:
            app.log.error("Necessário informar um taxonomy_name")
            return None, {'message':"Necessário informar um taxonomy_name", 'status_code': 400}

        if 'item_order' in new_taxonomy:
            if not new_taxonomy['item_order'].isdigit():
                app.log.error(f"item_order {new_taxonomy['item_order']}, não contem apenas numeros")
                return None, {'message': f"item_order' deve conter somente números.", 'status_code': 400}

            else:
                taxonomy['item_order'] = int(new_taxonomy['item_order'])   
        else:
            taxonomy['item_order'] = 0       

        if 'active' in new_taxonomy:
                if type(new_taxonomy['active']) is not bool:
                    app.log.error(f"{new_taxonomy['active']}, deve ser um booleano")
                    return None, {'message': "Active deve ser true ou false.", 'status_code': 400}

                else:
                    taxonomy['active'] = new_taxonomy['active']
        else:
            app.log.error("É necessario informar se o estado atual do item.")
            return None, {'message': "É necessario informar se o estado atual do item.", 'status_code': 400}

        if not 'parent_id' in new_taxonomy:
            if 'product_id' in new_taxonomy:
                product_id_validator = parser.check_uuid(new_taxonomy['product_id'])

                if not product_id_validator:
                    app.log.error(f"{new_taxonomy['product_id']} invalido")

                    return None, {'message': "O product_id é invalido", 'status_code': 400}
            else:
                app.log.error("É necessario informar o product_id do item.")
                return None, {'message': "É necessario informar o product_id do item.", 'status_code': 400}
            
            if 'initial_year' in new_taxonomy:
                taxonomy['initial_year'] = str(new_taxonomy['initial_year'])
            else:
                taxonomy['initial_year'] = str(datetime.now().year)

            if 'group_id' in new_taxonomy:
                group_id_validator = parser.check_uuid(new_taxonomy['group_id'])

                if not group_id_validator:
                    app.log.error(f"{new_taxonomy['group_id']} invalido")

                    return None, {'message': "O Group_id é invalido", 'status_code': 400}
                else:
                    taxonomy['group_id'] = new_taxonomy['group_id']
            else:
                app.log.error("É necessario informar o group_id do item.")
                return None, {'message': "É necessario informar o group_id do item.", 'status_code': 400}
        else:
            if 'group_id' in new_taxonomy:
                app.log.error("Uma pasta filha não deve ter group_id.")
                return None, {'message': "Uma pasta filha não deve ter group_id.", 'status_code': 400}

            if 'product_id' in new_taxonomy:
                app.log.error("Uma pasta filha não deve ter product_id.")
                return None, {'message': "Uma pasta filha não deve ter product_id.", 'status_code': 400}

            if 'initial_year' in new_taxonomy:
                app.log.error("Uma pasta filha não deve ter initial_year.")
                return None, {'message': "Uma pasta filha não deve ter initial_year.", 'status_code': 400}
            else:
                taxonomy['initial_year'] = None

        fields_to_check = ('taxonomy_description', 'link', 'telegram_url', 'instagram_url', 'vitreo_label', 'vitreo_link_type', 'vitreo_link','vitreo_app_link', 'vitreo_al_link', 'large_cover', 'small_cover', 'custom_avatar')
        for field_name in fields_to_check:
            taxonomy[field_name] = new_taxonomy.get(field_name, None)

        app.log.info("Sucesso na validação de dados")
        return taxonomy, {'message': "Sucesso na validação de dados", 'status_code': 200}

    except Exception as ex:
            app.log.error(f"Erro ao registrar pasta. Error: {ex}")
            return None, {'message': f"Erro ao registrar pasta. Error: {ex}", 'status_code': 400}
            
def post_taxonomy_postgres(taxonomy, new_taxonomy):

    try:
        sql_insert_taxonomy = """
            INSERT INTO "content".taxonomies (taxonomy_id, created_by, created_at, parent_id, name, slug, active, link, value, description, telegram_url, instagram_url, vitreo_label, vitreo_link, vitreo_link_type, vitreo_app_link, vitreo_al_link, initial_year, large_cover, small_cover, custom_avatar) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s, %s);
        """
        if taxonomy:
            conn, cursor = get_connection()

            app.log.info('Inserindo taxonomia no PostgreSQL')
            cursor.execute(sql_insert_taxonomy, (taxonomy['taxonomy_id'], taxonomy['created_by'], taxonomy['created_at'], taxonomy['parent_id'], taxonomy['taxonomy_name'], taxonomy['taxonomy_slug'], taxonomy['active'], taxonomy['link'],taxonomy['item_order'], taxonomy['taxonomy_description'], taxonomy['telegram_url'], taxonomy['instagram_url'], taxonomy['vitreo_label'], taxonomy['vitreo_link'], taxonomy['vitreo_link_type'], taxonomy['vitreo_app_link'], taxonomy['vitreo_al_link'], taxonomy['initial_year'],taxonomy['large_cover'], taxonomy['small_cover'], taxonomy['custom_avatar'],)) 

            conn.commit()    
        
        sql_insert_group_id = """
            INSERT INTO "content".taxonomies_groups (taxonomy_id, group_id) 
            VALUES (%s,%s);
        """
        if 'group_id' in taxonomy:

            app.log.info('Inserindo group_id no PostgreSQL')
            cursor.execute(sql_insert_group_id, (taxonomy['taxonomy_id'], taxonomy['group_id'],))
            conn.commit()    
        
        sql_insert_taxonomies_products = """
            INSERT INTO "content".taxonomies_products (taxonomy_id, product_id) 
            VALUES (%s,%s);
        """
        if 'product_id' in new_taxonomy:           
            app.log.info('Inserindo product_id no PostgreSQL')
            cursor.execute(sql_insert_taxonomies_products, (taxonomy['taxonomy_id'], new_taxonomy['product_id'],)) 
            conn.commit()    

        sql_insert_taxonomy_author = """
            INSERT INTO "content".taxonomies_authors (taxonomy_id, author_id) 
            VALUES (%s,%s);
        """
        if 'author_id' in new_taxonomy:   
            app.log.info('Inserindo author_id no PostgreSQL')
            cursor.execute(sql_insert_taxonomy_author, (taxonomy['taxonomy_id'], new_taxonomy['author_id'],)) 
            conn.commit()

        cursor.close()
        conn.close()
        
        taxonomy_return = {
            'taxonomy_id': taxonomy['taxonomy_id']
        }

        app.log.info(f"Taxonomia {taxonomy['taxonomy_id']} criada com sucesso.")
        return taxonomy_return, {'message': f"Taxonomia {taxonomy['taxonomy_id']} criada com sucesso.", 'status_code': 200}                
    
    except psycopg2.Error as pgsql_exception:
        conn.rollback()
        app.log.error(f"Erro ao conectar ao postgresql: {pgsql_exception}")
        return None, {'message': f"Erro ao conectar ao postgresql: {pgsql_exception}", 'status_code': 500}

    except Exception as ex:
         return None, {'message': f"Problemas ao gravar os dados. Error: {ex}", 'status_code': 500}        


def validate_put_taxonomy(updated_taxonomy):

    try:
        app.log.info('Iniciando validação de dados para edição de taxonomia.')
        if not updated_taxonomy:
            return None, {'message': f"Não foi enviado um Json", 'status_code': 500}
        
        invalid_key_in_body = ('parent_id', 'taxonomy_slug','parent_id')
        if invalid_key_in_body in updated_taxonomy.keys():
            app.log.error(f"Não deve-se mandar {invalid_key_in_body} para uma edição")
            return None, {'message': f"Não deve-se mandar {invalid_key_in_body} para uma edição", 'status_code': 400}

        if 'item_order' in updated_taxonomy:
            if not updated_taxonomy['item_order'].isdigit():
                app.log.error(f"{updated_taxonomy['item_order']}, deve ser número")
                return None, {'message': "O item_order deve ser um número", 'status_code': 400}

        if 'product_id' in updated_taxonomy:
            product_id_validator = parser.check_uuid(updated_taxonomy['product_id'])
            if not product_id_validator:
                app.log.error(f"{updated_taxonomy['product_id']} invalido")
                return None, {'message': "O product_id é invalido", 'status_code': 400}

        app.log.info('Validação para editar taxonomia concluida')  
        return updated_taxonomy, {'message': "Validação para editar taxonomia concluida", 'status_code': 200}

    except Exception as ex:
        app.log.error("Erro ao atualizar pasta")
        return None, {'message': f"Erro ao atualizar pasta. Error: {ex}", 'status_code': 400}

def put_taxonomy_postgres(updated_taxonomy, taxonomy_id, user_id):
    sql_update_taxonomy = """
        UPDATE "content".taxonomies t
        SET updated_by = %s, updated_at = %s, {column_name} = %s
        WHERE t.taxonomy_id = %s;
    """

    taxonomy = {
        'taxonomy_id': taxonomy_id,
        'updated_by': user_id,
        'updated_at': datetime.now()
    }

    try:
        fields = {'taxonomy_id': 'taxonomy_id', 'product_id': 'product_id', 'group_id':'group_id', 'item_order': 'value', 'taxonomy_name': 'name', 'active': 'active', 'taxonomy_description': 'description', 'link': 'link', 'telegram_url': 'telegram_url','instagram_url': 'instagram_url', 'vitreo_label': 'vitreo_label', 'vitreo_link': 'vitreo_link','vitreo_link_type':'vitreo_link_type','vitreo_app_link': 'vitreo_app_link','vitreo_al_link':'vitreo_al_link', 'large_cover': 'large_cover', 'small_cover':'small_cover','author_id':'author_id', 'custom_avatar': 'custom_avatar' }

        dict_with_postgre_name = {}
        
        for item in updated_taxonomy:
            dict_with_postgre_name[fields[item]] = updated_taxonomy[item]
    
        fields_to_check_in_taxonomy = ('name', 'active', 'link','value', 'telegram_url', 'instagram_url', 'vitreo_label', 'vitreo_link', 'vitreo_link_type', 'vitreo_app_link', 'vitreo_al_link', 'large_cover', 'small_cover', 'custom_avatar')

        conn, cursor = get_connection()

        if dict_with_postgre_name:   
            for key, value in dict_with_postgre_name.items():
                if key in fields_to_check_in_taxonomy:
                    sql_query = sql_update_taxonomy.format(column_name=key)
                    cursor.execute(sql_query, (taxonomy['updated_by'], taxonomy['updated_at'], value, taxonomy['taxonomy_id'],)) 
            conn.commit()    

        sql_update_group_id = """
            UPDATE "content".taxonomies_groups AS taxgroup
            SET group_id = %s 
            WHERE taxgroup.taxonomy_id = %s;
        """
        if 'group_id' in updated_taxonomy:
            cursor.execute(sql_update_group_id, (updated_taxonomy['group_id'], taxonomy_id))
            conn.commit()    

        sql_update_taxonomies_products = """
            UPDATE "content".taxonomies_products AS taxprod
            SET product_id = %s 
            WHERE taxprod.taxonomy_id = %s;
        """
        if 'product_id' in updated_taxonomy:
            cursor.execute(sql_update_taxonomies_products, (updated_taxonomy['product_id'],taxonomy_id,)) 
            conn.commit()    

        sql_update_taxonomy_author = """
            UPDATE "content".taxonomies_authors AS taxauth
            SET author_id = %s 
            WHERE taxauth.taxonomy_id = %s;
        """
        if 'author_id' in updated_taxonomy:   
            cursor.execute(sql_update_taxonomy_author, (updated_taxonomy['author_id'], taxonomy['taxonomy_id']))
            conn.commit()    

        cursor.close()
        conn.close()

        app.log.info(f'Taxonomia {taxonomy_id} atualizada com sucesso.')
        return taxonomy["taxonomy_id"], {'message': f"Taxonomia {taxonomy_id} atualizada com sucesso.", 'status_code': 200}    
      
    except psycopg2.Error as pgsql_exception:
        conn.rollback()
        app.log.error(f"Erro ao conectar ao postgresql: {pgsql_exception}")
        return None, {'message': f"Erro ao conectar ao postgresql: {pgsql_exception}", 'status_code': 500}

    except Exception as ex:
         return None, {'message': f"Problemas ao atualizar os dados. Error: {ex}", 'status_code': 500}        


def validate_update_order(updated_order):
    try:
        app.log.info('Iniciando ordenação de taxonomias.')
        if not updated_order:
            return None, {'message': f"Não foi enviado um Json", 'status_code': 500}

        sql_update_order_taxonomy = """
            UPDATE "content".taxonomies t
            SET value = %s
            WHERE t.taxonomy_id = %s;
        """
        sql_update_order_publication = """
            UPDATE "content".publications pub
            SET value = %s 
            WHERE pub.publication_id = %s;
        """

        conn, cursor = get_connection()
        for item in updated_order:
            if not item['item_order'].isdigit():
                    app.log.error(f"{item['item_order']}, deve ser número")
                    return None, {'message': "O item_order deve ser um número", 'status_code': 400}

            if 'publication_id' in item and 'item_order' in item:
                cursor.execute(sql_update_order_publication, (item['item_order'], item['publication_id'],)) 
                conn.commit()            

            elif 'taxonomy_id' in item and 'item_order' in item:
                cursor.execute(sql_update_order_taxonomy, (item['item_order'], item['taxonomy_id'],)) 
                conn.commit() 
        
        cursor.close()
        conn.close()          

        app.log.info("Item_order atualizados com sucesso.")
        return updated_order, {'message': "Item_order atualizados com sucesso.", 'status_code': 200}
    
    
    except psycopg2.Error as pgsql_exception:
        conn.rollback()
        app.log.error(f"Erro ao conectar ao postgresql: {pgsql_exception}")
        return None, {'message': f"Erro ao conectar ao postgresql: {pgsql_exception}", 'status_code': 500}

    except Exception as ex:
         return updated_order, {'message': f"Problemas ao atualizar os dados. Error: {ex}", 'status_code': 500}        
