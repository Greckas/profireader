import sys

sys.path.append('..')
from profapp.models.materials import Publication
from profapp.models.portal import MemberCompanyPortal
from profapp.models.elastic import elasticsearch


from profapp import create_app, load_database
import argparse


classes = [Publication, MemberCompanyPortal]


def recreate_documents():

    for aclass in classes:
        aclass.elastic_reindex_all()

    # for s in structure:
    #     s.recreate_all_documents()
    #     pass

    # for ei in indexes:
    #     ei.insert_all_documents()
    # for doctype, doc_properties in es.get_elastic_fields().items():
    #     id_field = doc_properties['id']
    #     main_class = list(id_field['depend_on'].keys())[0]
    #     for o in db_session.query(main_class).all():
    #         elastic_doc = {}
    #         for f_name, f_prop in doc_properties.items():
    #             elastic_doc[f_name] = f_prop['depend_on'][main_class][1](o)
    #
    #         es.add(doctype, doctype, o.id, elastic_doc)
    # db_session.commit()


def delete_indexes():
    elasticsearch.show_all_indexes()
    elasticsearch.remove_all_indexes()
    elasticsearch.show_all_indexes()


if __name__ == '__main__':
    # time = datetime.datetime.now()

    parser = argparse.ArgumentParser(description='profireader application type')
    parser.add_argument("whattodo", default='reindex')
    args = parser.parse_args()

    app = create_app(apptype='profi')
    with app.app_context():
        load_database(app.config['SQLALCHEMY_DATABASE_URI'])()

        if args.whattodo == 'delete_elastic_indexes':
            delete_indexes()

        elif args.whattodo == 'recreate_all_elastic_documents':
            recreate_documents()

